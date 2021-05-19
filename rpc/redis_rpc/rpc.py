# coding=utf-8
"""
@author:yuceyingjia
@date:2020/11/27
"""
import json
import uuid

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from ycyj_zhongtai.config.config_manage import ConfigManage
from ycyj_zhongtai.libs.exception.api_exception import ApiNotFoundException
from ycyj_zhongtai.libs.rpc.redis_rpc.base_worker import WorkerName
from ycyj_zhongtai.libs.rpc.redis_rpc.redis import YCYJRedisClient
from ycyj_zhongtai.libs.zookeeper.client import ZooKeeperClient


class WorkerContext(object):

    def __init__(self, redis=YCYJRedisClient()):
        self.redis = redis
        self.work_dic = dict()  # {'WorkerName':[version...]}
        self._init_worker_channel()
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._init_worker_channel, 'interval', seconds=60)
        logger.info('启动间隔60s定期获取服务配置信息')
        self.scheduler.start()

    def _init_worker_channel(self):
        """
        维护一个方法字典，从zookeeper中获取
        取网关版本数据，再取接口方法数据，过滤出版本最大的服务方法
        """
        with ZooKeeperClient() as zc:
            # 先找zk配置中心，如果zk配置中心没有再找本地配置文件

            worker_version = int(zc.get_val('/worker_version/' + WorkerName.AppGateWay))

            if worker_version < 50000:
                confobj = ConfigManage.get_val('worker_version')
                worker_version = confobj.get(WorkerName.AppGateWay, 50000)

            worker_name_ls = zc.get_children_ls('/ycyj_apis')  # 服务名列表
            worker_dic = {}
            for worker_name in worker_name_ls:
                # 取方法接口下的所有版本 与 网关最大版本比较，取最新的服务接口版本
                service_v_path = '/ycyj_apis/{worker_name}'.format(worker_name=worker_name)
                v_code_ls = zc.get_children_ls(service_v_path)  # 版本列表

                v_ls = []  # 用列表缓存是因为，返回的版本列表不是排序好的，需要手动排序
                for m_code in v_code_ls:
                    service_v_int = int(m_code)
                    if service_v_int >= worker_version:
                        v_ls.append(service_v_int)
                if len(v_ls) > 0:
                    v_ls.sort(reverse=True)
                    worker_dic[worker_name] = v_ls

            self.worker_dic = worker_dic

    def get_worker_channel(self, service_name, service_version):
        v_list = self.worker_dic.get(service_name, [])
        if len(v_list) > 0:
            if service_version and service_version in v_list:
                channel = f'work:{service_name}:{service_version}'
            else:
                channel = f'work:{service_name}:{v_list[0]}'
            return channel
        else:
            raise ApiNotFoundException(service_name)


class _ClusterRpcProxy(object):

    def __init__(self):
        self._worker_ctx = WorkerContext()
        self._proxies = {}

    def __getattr__(self, name):
        if name not in self._proxies:
            self._proxies[name] = ServiceProxy(name, self._worker_ctx)
        return self._proxies[name]


class ServiceProxy(object):

    def __init__(self, service_name='ServiceProxy', worker_ctx=None):
        self.service_name = service_name
        self.worker_ctx = worker_ctx

    def __getattr__(self, method_name):
        return MethodProxy(self.service_name, self.service_version, method_name, self.worker_ctx)

    def __call__(self, *args, **kwargs):
        if args and len(args) > 0:
            self.service_version = args[0]
        else:
            self.service_version = None
        return self


class MethodProxy(object):

    def __init__(self, service_name, service_version, method_name, worker_ctx):
        self.service_name = service_name
        self.service_version = service_version
        self.method_name = method_name
        self.worker_ctx = worker_ctx

    def random_key(self):
        return str(uuid.uuid4())

    def __call__(self, *args, **kwargs):
        id = self.random_key()
        if not args:
            args = None
        params_val = args

        if kwargs is not None and kwargs != {}:
            params_val = kwargs

        queue_name = self.worker_ctx.get_worker_channel(self.service_name, self.service_version)
        request = {'id': id,
                   'queue_name': queue_name,
                   'method': self.method_name,
                   'params': params_val}

        logger.debug('request = {}'.format(request))

        self.worker_ctx.redis.lpush(queue_name, json.dumps(request))
        # 只要有调用，就会顺延时间，如果时间不过期历史的会保留
        # 不考虑后端处理超时情况
        self.worker_ctx.redis.expire(queue_name, 15)
        channel, response = self.worker_ctx.redis.brpop(id, 15)  # 如果超时会抛异常
        return response.decode('utf-8')


rpc_proxy = _ClusterRpcProxy()
