import _thread
import ast
import inspect
import time
import uuid
from concurrent.futures.thread import ThreadPoolExecutor
import json
from loguru import logger
from redis import Redis

from ycyj_zhongtai.config.config_manage import ConfigManage
from ycyj_zhongtai.libs.exception.api_exception import ApiException, ApiNotFoundException, ApiArgumentException
from ycyj_zhongtai.libs.log.log_ext import init_logger
from ycyj_zhongtai.libs.zookeeper.client import ZooKeeperClient
from ycyj_zhongtai.libs.rpc.redis_rpc.exceptions import ParaFormatError
from ycyj_zhongtai.libs.rpc.redis_rpc.redis import YCYJRedisClient
from ycyj_zhongtai.libs.value_convert_type_ext import to_bool

def no_reg(func):
    """
    不进行服务注册
    """

    def decorated(*args, **kwargs):
        return func(*args, **kwargs)

    return decorated


class WorkerRegister:
    """
    服务注册
    """
    cache_method_dic = {}  # {'方法名':'函数'}

    def __init__(self):
        self.version = -1  # 与api_version 对应例如：40100 表示v4.1.0
        self.queue_name = ''
        self.worker_name = ''

    def _register(self, *args):
        """
        注册对象为服务
        参数为，对象，例如：
        ServiceWorker()._register(LoginBiz())._start_worker_with_thread(WorkerName.user)
        """
        if args is None:
            args = []
        args = list(args)

        # 遍历对象数组里的所有对外方法
        for obj in args:
            ms = self._get_methods(obj)
            for m in ms:
                if m not in WorkerRegister.cache_method_dic:
                    WorkerRegister.cache_method_dic[m] = obj.__getattribute__(m)
        return self

    def _get_methods(self, obj):
        target = type(obj)
        methods = []

        def visit_FunctionDef(node):
            if not node.name.startswith("_") and not node.name.endswith("_"):
                is_exist = True
                # 获取装饰器列表
                for n in node.decorator_list:
                    name = ''
                    if isinstance(n, ast.Call):
                        name = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                        print(n.func.id)
                    else:
                        name = n.attr if isinstance(n, ast.Attribute) else n.id
                    if name == no_reg.__name__:
                        is_exist = False
                if is_exist:
                    methods.append(node.name)

        node_iter = ast.NodeVisitor()
        node_iter.visit_FunctionDef = visit_FunctionDef
        node_iter.visit(ast.parse(inspect.getsource(target)))
        return methods



    def _set_service(self):
        # 设置服务注册
        zc = ZooKeeperClient()
        zc.start()
        channel_uid = str(uuid.uuid4())
        path = '/ycyj_apis/{}/{}/{}'.format(self.worker_name, self.version, channel_uid)
        zc.set_val(path, channel_uid, ephemeral=True)

    def _check_input(self):
        if self.queue_name == '':
            raise Exception('self.queue_name 没有设置')
        if self.version < 0:
            raise Exception('self.version 没有设置')

    def _register_to_zookeeper(self, version, queue_name):
        self.version = version
        self.queue_name = queue_name
        self._check_input()
        self._set_service()


class BaseWorker(WorkerRegister):
    cache_varname_dic = {}

    def __init__(self, redis=Redis()):
        super(BaseWorker, self).__init__()
        self.redis = redis
        self.worker_name = ''
        self.version = 0
        self.thread_pool = ThreadPoolExecutor(100)

    def _work_queue(self):
        return 'work:{}:{}'.format(self.worker_name, self.version)

    def _start_worker(self, worker_name, worker_version, is_break=False):
        """
        启动worker
        :param version 服务版本号，必须指定
        :param argv 系统参数，部署时传入
        :param is_break 是否跳过，单元测试用
        """
        self.worker_name = worker_name
        self.version = worker_version
        init_logger(self.worker_name)
        logger.info("Running worker: {}".format(self.worker_name))
        logger.info('注册服务到ZooKeeper中, queue_name=>{}'.format(self._work_queue()))
        self._register_to_zookeeper(self.version, self._work_queue())

        logger.info("Monitoring {}, redis:{}".format(self._work_queue(), self.redis))
        while True:
            if is_break:
                break
            try:
                channel, request = self.redis.brpop(self._work_queue())
                self.thread_pool.submit(self._process_pool, request)
            except Exception as ex:
                logger.exception(ex)
                time.sleep(5)

    def _start_worker_with_thread(self, worker_name, is_break=False):
        # 启动业务worker
        worker_version = ConfigManage.get_val('worker_version')[worker_name]
        _thread.start_new_thread(self._start_worker, (worker_name, worker_version, is_break))

    def _process_pool(self, request):
        request_data = json.loads(request)
        self._process_request(request_data)

    def _log_request(self, request):
        logger.debug(request)

    def _get_state(self, ex):
        """
        获取错误吗
        :param ex:
        :param func_name: 函数名
        :return:
        """
        r = 0
        if isinstance(ex, ApiException):
            r = ex.state
        else:
            r = 0
        return r

    def _redis_rpush(self, request_id, r_dict):
        self.redis.rpush(request_id, json.dumps(r_dict, ensure_ascii=False))
        self.redis.expire(request_id, 15)

    def _check_match_params(self, func, **kwargs):
        """
        检查参数是否匹配
        """
        try:
            inspect.signature(func).bind(**kwargs)
        except TypeError as e:
            raise ApiArgumentException()
        except Exception as e:
            pass

    def _process_request(self, request):
        entry_span = None
        try:
            self._log_request(request)
            request_id = request['id']
            queue_name = request['queue_name']
            method = request['method']
            args = request['params']

            entry_span_op = ''
            r_dict = {'ID': request_id, 'State': 1, 'Msg': 'success', 'Data': '', 'Count': 0}
            try:
                biz_func = None
                if method in BaseWorker.cache_method_dic:
                    biz_func = BaseWorker.cache_method_dic[method]
                else:
                    raise ApiNotFoundException(method)

                if args:
                    if isinstance(args, dict):
                        if method in BaseWorker.cache_varname_dic:
                            varname_dic = BaseWorker.cache_varname_dic[method]
                        else:
                            varname_dic = inspect.signature(biz_func).parameters
                            BaseWorker.cache_varname_dic[method] = varname_dic

                        for param in varname_dic:
                            if param in args:
                                try:
                                    parameter_type = varname_dic[param].annotation  # 获取参数冒号后面 类型
                                    if parameter_type is bool:
                                        args[param] = to_bool(args[param])

                                    elif isinstance(parameter_type, type) and inspect._empty is not parameter_type:
                                        args[param] = parameter_type(args[param])

                                except Exception as ex:
                                    logger.info(ex)
                                    raise ParaFormatError(ex.__str__())

                        del_keys = []
                        for k in args:
                            if k not in varname_dic:
                                del_keys.append(k)
                        for k in del_keys:
                            del args[k]

                        self._check_match_params(func=biz_func, **args)

                        r_dict['Data'] = biz_func(**args)

                        if isinstance(r_dict['Data'], list):
                            r_dict['Count'] = len(r_dict['Data'])
                    else:
                        r_dict['Data'] = biz_func(*args)
                        if isinstance(r_dict['Data'], list):
                            r_dict['Count'] = len(r_dict['Data'])
                else:
                    r_dict['Data'] = biz_func()
                    if isinstance(r_dict['Data'], list):
                        r_dict['Count'] = len(r_dict['Data'])
            except Exception as ex:
                state_val = self._get_state(ex)
                r_dict['State'] = state_val
                r_dict['Msg'] = str(ex)
                if state_val == 0:
                    logger.exception(ex)  # 只有未知异常才记录，其他异常记录警告日志
                else:
                    logger.warning(ex)
            self._redis_rpush(request_id, r_dict)
        except Exception as ex:
            logger.exception(ex)



class ServiceWorker(BaseWorker):
    """
    服务worker，添加一层，控制连接地址
    可重写方法，加入链路监控插件等
    """

    def __init__(self):
        super(ServiceWorker, self).__init__(YCYJRedisClient())


class WorkerName:
    """
    子系统服务名， 对应配置文件里的 worker_version配置
    """

    AppGateWay = 'AppGateWay'
    WSGateWay = 'WSGateWay'

    CRMApi = 'CRMApi'
    CRMServer = 'CRMServer'

    UserApi = 'UserApi'
    UserServer = 'UserServer'

    STYJApi = 'STYJApi'  # 证通赢家
    STYJServer = 'STYJServer'

    YCYJSubSysApi = 'SubSysApi'  # 赢家子系统
    YCYJSubSysServer = 'SubSysServer'

    YCYJF10Api = 'F10Api'  # F10 模块
    YCYJF10ApiDev = 'F10ApiDev'  # F10 模块测试
    YCYJF10Server = 'F10Server'


    YCYJGongShiApi = 'GongShiApi'  # 公式数据
    YCYJGongShiServer = 'GongShiServer'

    YCYJHQApi = 'HQApi'  # 行情数据
    YCYJHQServer = 'HQServer'
    YCYJHQSocket = 'HQSocket'  #web socket

    YCYJTradeApi = 'TradeApi'  # 交易模块
    YCYJTradeServer = 'TradeServer'

    YCYJMockTradeApi = 'MockTradeApi'  # 模拟交易模块
    YCYJMockTradeServer = 'MockTradeServer'  # 模拟交易服务

    YCYJTJDApi = 'TJDApi'  # 条件单Api
    YCYJTJDServer = 'TJDServer'  # 条件单Server

    ShuJuShouJiApi = 'ShuJuShouJiApi'  # 数据收集api
    ShuJuShouJiServer = 'ShuJuShouJiServer'  # 数据收集服务

    YuJingServer = 'YuJingServer'
    TJYuJingServer = 'TJYuJingServer'

    YCYJXSXTApi = 'XSXTApi'  # 相似形态