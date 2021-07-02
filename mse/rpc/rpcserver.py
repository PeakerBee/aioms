# coding=utf-8
"""
@Time : 2021/6/18 10:12 
@Author : Peaker
"""
import json
import time
import uuid
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any, Dict, Optional, Type, Union

from redis import Redis
from tornado.routing import _RuleList
from discovery.instance import ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from logger.log import gen_log
from mse.rpc.routing import RuleRouter
from mse.rpc.rpcutil import RpcMessageDelegate, RpcServerRequest
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
            server: 'RpcServer',
            request: 'RpcServerRequest',
            **kwargs: 'Any'):
        self.server = server
        self.request = request
        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        """subclass override for initialization. Called for each request."""
        pass

    def execute(self):
        result = self.handler.handle_request()

    def write(self, chunk: Union[str, bytes, dict]) -> None:
        pass

    def handle_request(self) -> Union[str, bytes, dict]:
        """subclass must implement the method for handle rpc request and return data"""
        raise NotImplementedError()


class _HandlerDelegate(RpcMessageDelegate):

    def __init__(
            self,
            server: 'RpcServer',
            request: 'RpcServerRequest',
            handler_class: 'Type[RequestHandler]',
            handler_kwargs: Optional[Dict[str, Any]], ):
        self.server = server
        self.request = request
        self.handler_class = handler_class
        self.handler_kwargs = handler_kwargs

    def execute(self):
        self.handler = self.handler_class(
            self.server, self.request, **self.handler_kwargs
        )
        self.handler.execute()




class RpcServer(Application, RuleRouter):

    def __init__(self, handlers: '_RuleList' = None, config_path: 'str' = None):
        super(RpcServer, self).__init__(config_path=config_path)
        self.handlers = handlers
        self.thread_pool = ThreadPoolExecutor(50)
        host = self.context.get_redis_config().host
        pwd = self.context.get_redis_config().password
        self.redis = Redis(host=host, password=pwd, retry_on_timeout=True)

    def start(self) -> None:
        if self.service_name is None:
            raise CommonException(CommonErrorCode.NameNoSetting_Error)

        self.service_registry.start()
        self.service_registry.register_service(self.create_service_instance())
        self.listen()

    def _create_channel(self):
        return f'rpc:channel:{self.service_name}:{self.version}'

    def listen(self):
        self._read_message()

    def _read_message(self):
        while True:
            try:
                channel, request = self.redis.brpop(self._create_channel())
                self.thread_pool.submit(self._handle_request, request)
            except Exception as ex:
                gen_log.exception(ex)
                time.sleep(5)

    def _handle_request(self, request: 'Dict'):

        return_id = request['id']
        method = request['method']
        kwargs = request['params']

        request = RpcServerRequest(return_id=return_id, method=method, kwargs=kwargs)

        handler = self.find_handler(request)
        # handler.

    def find_handler(self, request: 'RpcServerRequest', **kwargs: Any) -> RpcMessageDelegate:
        pass

    def get_target_delegate(self) -> RpcMessageDelegate:
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
