import uuid
from abc import ABC
from enum import Enum
from http.server import HTTPServer
from typing import Any
from tornado import web
from tornado.ioloop import IOLoop
from tornado.routing import _RuleList

from discovery.instance import ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from mse.context import create_app_context
from mse.exceptions import ServiceRegistryError, ConfigNotSettingError
from mse.factory import ServiceRegistryFactory
from mse.utils import get_local_ip
from zookeeper.discovery import ZookeeperServiceInstance


class RouteType(Enum):
    HTTP = 1
    REDIS_RPC = 2


class Application(ABC):

    def __init__(
            self,
            handlers: _RuleList = None,
            address: str = '0.0.0.0',
            config_path: 'str' = None,
            **settings: Any
    ) -> None:
        self.handlers = handlers
        self.default_application = web.Application(self.handlers, settings=settings)
        if config_path is None:
            raise ConfigNotSettingError()

        self.context = create_app_context(config_path)

        discovery_config = self.context.get_discovery_config()

        if discovery_config is None:
            raise CommonException(error_code=CommonErrorCode.Discovery_Conf_Not_Setting_Error)

        service_provider_factory = ServiceRegistryFactory()
        self.service_registry = service_provider_factory.apply(discovery_config)

        if self.service_registry is None:
            raise ServiceRegistryError()

        self.service_name = self.context.get_app_name()
        self.port = self.context.get_port()
        self.address = address
        self.version = self.context.get_version()

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

    def create_service_instance(self) -> 'ServiceInstance':
        instance_id = str(uuid.uuid4())
        service_id = self.service_name
        host = get_local_ip()
        port = self.port
        service = ZookeeperServiceInstance(instance_id=instance_id, service_id=service_id,
                                           host=host, port=port,
                                           version=self.version,
                                           rpc_type=RouteType.HTTP.value,
                                           metadata=dict())

        return service

