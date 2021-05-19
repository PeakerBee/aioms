# coding=utf-8
import json
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from ycyj_zhongtai.config.config_manage import ConfigManage
from ycyj_zhongtai.gateway.app.exception import WorkerTimeoutError, VersionFormatError, VersionNumTooTowError
from ycyj_zhongtai.gateway.throttle.throttling import TokenBucketThrottle
from ycyj_zhongtai.libs.exception.api_exception import ApiNotFoundException, ApiFormatErrorException
from ycyj_zhongtai.libs.rpc.rpc_client import RpcClient
from ycyj_zhongtai.libs.rpc.redis_rpc.redis import YCYJRedisClient
from ycyj_zhongtai.libs.zookeeper.client import ZooKeeperClient


class ServiceRpcClient(RpcClient):
    """
    服务端rpc客户端包装类
    控制连接地址
    """

    def __init__(self, worker_name):
        """
        :param worker_name 网关和服务都是 worker
        """
        super(ServiceRpcClient, self).__init__(YCYJRedisClient())
        self.worker_name = worker_name
        self.min_version = 50000
        self.worker_dic = dict()
        self._get_channel_dic()
        self.scheduler = BackgroundScheduler()
        self.throttling = TokenBucketThrottle(self.redis)
        self.scheduler.add_job(self._get_channel_dic, 'interval', seconds=10, coalesce=True, misfire_grace_time=60*5, max_instances=5)
        logger.info('启动间隔30s定期获取推送服务配置!')
        self.scheduler.start()

    def _get_channel_dic(self):
        """
        维护一个方法字典，从zookepper中获取
        取网关版本数据，再取接口方法数据，过滤出版本最大的服务方法
        """
        with ZooKeeperClient() as zc:
            # 先找zk配置中心，如果zk配置中心没有再找本地配置文件

            self.min_version = int(zc.get_val('/worker_version/' + self.worker_name))

            if self.min_version < 50000:
                confobj = ConfigManage.get_val('worker_version')
                self.min_version = confobj.get(self.worker_name, 50000)

            if self.min_version < 50000:
                self.min_version = 50000

            worker_name_ls = zc.get_children_ls('/ycyj_apis')  # 服务名列表
            worker_dic = dict()
            for worker_name in worker_name_ls:
                # 取方法接口下的所有版本 与 网关最大版本比较，取最新的服务接口版本
                service_v_path = '/ycyj_apis/{worker_name}'.format(worker_name=worker_name)
                v_code_ls = zc.get_children_ls(service_v_path)  # 版本列表
                v_ls = []  # 用列表缓存是因为，返回的版本列表不是排序好的，需要手动排序
                for m_code in v_code_ls:
                    if not m_code.isdigit():
                        continue
                    channel_ids = zc.get_children_ls('/ycyj_apis/{}/{}'.format(worker_name, m_code))
                    service_v_int = int(m_code)
                    if channel_ids is not None and \
                            len(channel_ids) > 0 and \
                            service_v_int >= self.min_version > 0:
                        v_ls.append(service_v_int)
                if len(v_ls) > 0:
                    v_ls.sort(reverse=True)
                    worker_dic[worker_name] = v_ls

            self.worker_dic = worker_dic
            logger.info(f'worker_dic = {self.worker_dic}')

    def get_json(self, api_name, *params, **kwargs):
        """
        同步调用
        """
        method_names = api_name.split('/')
        if len(method_names) > 2:
            method_name = method_names[2]
            api_name = method_names[0]
            try:
                version = int(method_names[1])
            except ValueError as ex:
                raise VersionFormatError()

        else:
            raise ApiFormatErrorException(api_name)

        if version < self.min_version:
            raise VersionNumTooTowError(api_name)

        v_list = self.worker_dic.get(api_name, [])

        if len(v_list) > 0:
            if version in v_list:
                channel = f'work:{api_name}:{version}'
            else:
                channel = f'work:{api_name}:{v_list[0]}'

        else:
            raise ApiNotFoundException(api_name)

        logger.info('request channel = {}'.format(channel))

        id = self.send_request(None, channel, method_name,
                               *params, **kwargs)
        try:
            jstr = self.get_response(id)
            return jstr
        except Exception:
            msg = f'接口{api_name}/{version}/{method_name}请求超时'
            raise WorkerTimeoutError(msg=msg)

    def throttling_if_need(self, worker_name, method_name, ip):
        if worker_name and method_name and ip:
            if worker_name == 'UserApi' and method_name == 'GetSMSCode':
                self.throttling.allow_request(f'{ip}:{worker_name}:{method_name}')


    def get_result(self, api_name, *params, **kwargs):
        return json.loads(self.get_json(api_name, *params, **kwargs))
