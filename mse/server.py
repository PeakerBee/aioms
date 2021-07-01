# coding=utf-8
"""
@Time : 2021/7/1 13:49 
@Author : Peaker
"""
from abc import ABC
from enum import Enum
from http.server import HTTPServer
from tornado.ioloop import IOLoop

from discovery.instance import ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from mse.context import create_app_context
from mse.exceptions import ConfigNotSettingError, ServiceRegistryError
from mse.factory import ServiceRegistryFactory


class RouteType(Enum):
    HTTP = 1
    REDIS_RPC = 2


class Application(ABC):

    def __init__(self, config_path: 'str' = None) -> None:
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
        self.version = self.context.get_version()

    def start(self) -> None:

        if self.service_name is None:
            raise CommonException(CommonErrorCode.NameNoSetting_Error)

        self.service_registry.start()
        self.service_registry.register_service(self.create_service_instance())
        self.listen()
        IOLoop.instance().start()

    def listen(self) -> HTTPServer:
        raise NotImplementedError()

    def create_service_instance(self) -> 'ServiceInstance':
        raise NotImplementedError()





