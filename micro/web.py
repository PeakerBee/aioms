import socket
import uuid
from http.server import HTTPServer
from typing import Any
from tornado import web
from tornado.ioloop import IOLoop
from tornado.routing import _RuleList

from ycyj_zhongtai.gateway.app.discovery import ZookeeperServiceInstance
from ycyj_zhongtai.libs.discovery.instance import ServiceInstance
from ycyj_zhongtai.libs.exception.base import CommonException, CommonErrorCode
from ycyj_zhongtai.libs.micro.registry import ZookeeperServiceRegistry
from ycyj_zhongtai.libs.zookeeper.client import ZookeeperMicroClient


class Application:

    def __init__(
            self,
            handlers: _RuleList = None,
            name: str = None,
            address: str = '0.0.0.0',
            port: int = 0,
            root_path: str = '/micro-service',
            **settings: Any
    ) -> None:
        self.handlers = handlers
        self.default_application = web.Application(self.handlers, settings=settings)
        self.service_registry = ZookeeperServiceRegistry(zookeeper=ZookeeperMicroClient(), root_path=root_path)
        self.service_name = name
        self.port = port
        self.address = address

    def start(self) -> None:

        if self.service_name is None:
            raise Exception()

        self.service_registry.start()
        self.service_registry.register_service(self._create_service_instance())
        self.listen()
        IOLoop.instance().start()

    def listen(self) -> HTTPServer:

        if self.port == 0:
            raise CommonException(CommonErrorCode.PortNoSetting_Error)

        if self.default_application is None:
            raise Exception()
        return self.default_application.listen(port=self.port, address=self.address)

    def _create_service_instance(self) -> 'ServiceInstance':

        instance_id = str(uuid.uuid4())
        service_id = self.service_name
        host = self._get_local_ip()
        port = self.port
        service = ZookeeperServiceInstance(instance_id=instance_id, service_id=service_id, host=host, port=port, metadata=dict())

        return service

    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
