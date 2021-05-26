# coding=utf-8
import os
import sys

import tornado
import yaml
from tornado.ioloop import IOLoop
from tornado.routing import AnyMatches, Rule
from tornado.web import RequestHandler

from discovery.service import DiscoveryClient
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from gateway.config import config, ConfigOption, DiscoveryConfig
from gateway.filters import LoadBalancerClientFilter, AuthGatewayFilter, RequestRateLimiterGatewayFilter, \
    ForwardRoutingFilter
from gateway.handler import FilteringWebHandler, RequestForwardingHandler
from gateway.route.locator import RouteDefinitionRouteLocator, DiscoveryClientRouteDefinitionLocator
from logger.log import gen_log
from zookeeper.client import ZookeeperMicroClient
from zookeeper.discovery import ZookeeperDiscoveryClient


class DiscoveryFactory:

    def apply(self, conf: 'DiscoveryConfig') -> 'DiscoveryClient':
        """
        Discovery Factory Class responsible for creating DiscoveryClient according to the config
        """

        if conf.name == 'zookeeper':
            discovery_client = ZookeeperDiscoveryClient(ZookeeperMicroClient(hosts=conf.url), root_path=conf.root_path)
            return discovery_client


class Gateway:

    def __init__(self, port: int = 80, service_name: str = 'GateWay'):
        self.handlers = None
        self.config_option = config  # type: [ConfigOption]
        self.port = port
        self.service_name = service_name
        self.default_router = None

    def set_argv(self, argv):
        # 设置参数
        gen_log.warning('argv:{}'.format(argv))
        if len(argv) >= 2:
            self.port = argv[1]
        self.check_port()

    def check_port(self):
        if self.port == 0:
            raise CommonException(CommonErrorCode.PortNoSetting_Error)

    def start(self, argv):
        self.set_argv(argv)
        application = tornado.web.Application(self.handlers)
        application.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


class AppGateway(Gateway):

    def __init__(self):
        super(AppGateway, self).__init__()
        discovery_factory = DiscoveryFactory()
        discovery_config = self.config_option.get_discovery_config()

        if discovery_config is None:
            raise CommonException(error_code=CommonErrorCode.Discovery_Conf_Not_Setting_Error)

        self.discovery_client = discovery_factory.apply(self.config_option.get_discovery_config())
        self.route_definition_locator = DiscoveryClientRouteDefinitionLocator(self.discovery_client)
        self.route_locator = RouteDefinitionRouteLocator(route_def_locator=self.route_definition_locator)
        filters = [AuthGatewayFilter(), LoadBalancerClientFilter(),
                   RequestRateLimiterGatewayFilter(), ForwardRoutingFilter()]
        self.web_handler = FilteringWebHandler(filters=filters)
        self.handlers = [Rule(AnyMatches(), RequestForwardingHandler,
                              {'web_handler': self.web_handler, 'route_locator': self.route_locator})]


if __name__ == '__main__':
    AppGateway().start(sys.argv)
