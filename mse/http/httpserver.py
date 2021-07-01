import uuid
from typing import Any

from tornado import web
from tornado.httpserver import HTTPServer
from tornado.routing import _RuleList
from discovery.instance import ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from mse.server import RouteType, Application
from mse.utils import get_local_ip
from zookeeper.discovery import ZookeeperServiceInstance


class HttpServer(Application):

    def __init__(
            self,
            handlers: '_RuleList' = None,
            address: str = '0.0.0.0',
            config_path: 'str' = None,
            **settings: Any):
        super().__init__(config_path=config_path)
        self.address = address
        self.handlers = handlers
        self.default_application = web.Application(self.handlers, settings=settings)

    def listen(self) -> HTTPServer:
        if self.port == 0:
            raise CommonException(CommonErrorCode.PortNoSetting_Error)
        return self.default_application.listen(port=self.port, address=self.address)

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
