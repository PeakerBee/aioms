import socket
import uuid
from abc import ABC
from enum import Enum
from http.server import HTTPServer
from typing import Any, Union, List
from tornado import web
from tornado.ioloop import IOLoop
from tornado.routing import _RuleList

from discovery.instance import ZookeeperServiceInstance, ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from micro.registry import ZookeeperServiceRegistry
from zookeeper.client import ZookeeperMicroClient


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


class RouteType(Enum):
    HTTP = 1
    REDIS_RPC = 2


Handlers = Union[_RuleList, List[Any]]

class Application(ABC):

    def __init__(
            self,
            handlers: _RuleList = None,
            name: str = None,
            address: str = '0.0.0.0',
            port: int = 0,
            root_path: str = '/micro-service',
            version: int = 50000,
            **settings: Any
    ) -> None:
        self.handlers = handlers
        self.default_application = web.Application(self.handlers, settings=settings)
        self.service_registry = ZookeeperServiceRegistry(zookeeper=ZookeeperMicroClient(), root_path=root_path)
        self.service_name = name
        self.port = port
        self.address = address
        self.version = version

    def start(self) -> None:

        if self.service_name is None:
            raise CommonException(CommonErrorCode.NameNoSetting_Error)

        self.service_registry.start()
        self.service_registry.register_service(self.create_service_instance())
        self.listen()
        IOLoop.instance().start()

    def listen(self) -> HTTPServer:
        if self.port == 0:
            raise CommonException(CommonErrorCode.PortNoSetting_Error)
        return self.default_application.listen(port=self.port, address=self.address)

    def create_service_instance(self) -> 'ServiceInstance':
        raise NotImplementedError()


class HttpServer(Application):

    def __init__(
            self,
            handlers: _RuleList = None,
            name: str = None,
            address: str = '0.0.0.0',
            port: int = 0,
            root_path: str = '/micro-service',
            version: int = 50000,
            **settings: Any
    ) -> None:
        self.handlers = handlers
        self.default_application = web.Application(settings=settings)
        self.service_registry = ZookeeperServiceRegistry(zookeeper=ZookeeperMicroClient(), root_path=root_path)
        self.service_name = name
        self.port = port
        self.address = address
        self.version = version

    def create_service_instance(self) -> 'ServiceInstance':
        instance_id = str(uuid.uuid4())
        service_id = self.service_name
        host = get_local_ip()
        port = self.port
        service = ZookeeperServiceInstance(instance_id=instance_id, service_id=service_id,
                                           host=host, port=port,
                                           version=self.version,
                                           route_type=RouteType.HTTP.value,
                                           metadata=dict())

        return service


class RpcServer(Application):


    def __init__(
            self,
            handlers: _RuleList = None,
            name: str = None,
            address: str = '0.0.0.0',
            port: int = 0,
            root_path: str = '/micro-service',
            version: int = 50000,
            **settings: Any
    ) -> None:
        self.handlers = handlers
        self.default_application = web.Application(self.handlers, settings=settings)
        self.service_registry = ZookeeperServiceRegistry(zookeeper=ZookeeperMicroClient(), root_path=root_path)
        self.service_name = name
        self.port = port
        self.address = address
        self.version = version

    def create_service_instance(self) -> 'ServiceInstance':
        instance_id = str(uuid.uuid4())
        service_id = self.service_name
        host = get_local_ip()
        port = self.port
        service = ZookeeperServiceInstance(instance_id=instance_id, service_id=service_id,
                                           host=host, port=port,
                                           version=self.version,
                                           route_type=RouteType.REDIS_RPC.value,
                                           metadata=dict())

        return service
