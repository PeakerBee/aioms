# coding=utf-8
"""
@Time : 2021/6/18 10:12 
@Author : Peaker
"""
import time
import uuid
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any

from redis import Redis
from tornado.routing import _RuleList
from discovery.instance import ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from logger.log import gen_log
from mse.rpc.rpcutil import RpcMessageDelegate
from mse.server import RouteType, Application
from mse.utils import get_local_ip
from zookeeper.discovery import ZookeeperServiceInstance


class RequestHandler:
    """Base class for redis rpc request handler.

    Application should not construct `RequestHandler` objects
    directly and subclasses should not override ``__init__``
     (override`~RequestHandler.initialize` instead).

    """

    def __init__(
            self,
            application: 'Application',
            request: 'RpcServerRequest',
            **kwargs: 'Any'):
        self.application = application
        self.request = request
        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        """subclass override for initialization. Called for each request."""
        pass

    def handle_request(self):
        """subclass must implement the method for handle rpc request and return data"""
        raise NotImplementedError()


class _HandlerDelegate(RpcMessageDelegate):
    pass


class RpcServer(Application):

    def __init__(self, handlers: '_RuleList' = None, config_path: 'str' = None):
        super(RpcServer, self).__init__(config_path=config_path)
        self.handlers = handlers
        self.thread_pool = ThreadPoolExecutor(50)

    def start(self) -> None:
        if self.service_name is None:
            raise CommonException(CommonErrorCode.NameNoSetting_Error)

        self.service_registry.start()
        self.service_registry.register_service(self.create_service_instance())
        self.listen()

    def _create_channel(self):
        return f'rpc:channel:{self.service_name}:{self.version}'

    def listen(self):
        host = self.context.get_redis_config().host
        pwd = self.context.get_redis_config().password
        redis = Redis(host=host, password=pwd, retry_on_timeout=True)
        while True:
            try:
                channel, request = redis.brpop(self._create_channel())
                self.thread_pool.submit(self._handle_request, request)
            except Exception as ex:
                gen_log.exception(ex)
                time.sleep(5)

    def _handle_request(self, request):
        # request_id = request['id']
        # queue_name = request['queue_name']
        # method = request['method']
        # args = request['params']
        pass

    def create_service_instance(self) -> 'ServiceInstance':
        instance_id = str(uuid.uuid4())
        service_id = self.service_name
        host = get_local_ip()
        port = self.port
        metadata = dict()
        metadata['redis_host'] = self.context.get_redis_config().host
        metadata['password'] = self.context.get_redis_config().password
        metadata['user'] = self.context.get_redis_config().user
        service = ZookeeperServiceInstance(instance_id=instance_id, service_id=service_id,
                                           host=host, port=port,
                                           version=self.version,
                                           rpc_type=RouteType.REDIS_RPC.value,
                                           metadata=metadata)

        return service
