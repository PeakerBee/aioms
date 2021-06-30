# coding=utf-8
import sys
import tornado
from tornado.ioloop import IOLoop
from tornado.routing import AnyMatches, Rule
from tornado.web import RequestHandler
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from gateway.context import create_app_context
from gateway.filters import LoadBalancerClientFilter, AuthGatewayFilter, RequestRateLimiterGatewayFilter, \
    ForwardRoutingFilter
from gateway.handler import FilteringWebHandler, RequestForwardingHandler
from gateway.route.locator import RouteDefinitionRouteLocator, DiscoveryClientRouteDefinitionLocator
from logger.log import gen_log


class Gateway:

    def __init__(self):
        self.handlers = None
        self.app_context = create_app_context()
        self.port = self.app_context.get_port()
        self.service_name = self.app_context.get_app_name()
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
        self.route_definition_locator = DiscoveryClientRouteDefinitionLocator(self.app_context)
        self.route_locator = RouteDefinitionRouteLocator(route_def_locator=self.route_definition_locator)
        filters = [AuthGatewayFilter(), LoadBalancerClientFilter(),
                   RequestRateLimiterGatewayFilter(self.app_context), ForwardRoutingFilter()]
        self.web_handler = FilteringWebHandler(filters=filters)
        self.handlers = [Rule(AnyMatches(), RequestForwardingHandler,
                              {'web_handler': self.web_handler, 'route_locator': self.route_locator})]


if __name__ == '__main__':
    AppGateway().start(sys.argv)
