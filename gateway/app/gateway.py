# coding=utf-8
import sys

import tornado
from tornado.ioloop import IOLoop
from tornado.routing import AnyMatches, Rule
from tornado.web import RequestHandler
from loguru import logger
from ycyj_zhongtai.gateway.app.config import ZookeeperMicroServicePath
from ycyj_zhongtai.gateway.app.discovery import DiscoveryClientRouteDefinitionLocator, ZookeeperDiscoveryClient
from ycyj_zhongtai.gateway.app.filter import AuthGatewayFilter, RequestRateLimiterGatewayFilter, ForwardRoutingFilter, \
    LoadBalancerClientFilter
from ycyj_zhongtai.gateway.app.handler import RequestForwardingHandler, FilteringWebHandler
from ycyj_zhongtai.gateway.route.locator import RouteDefinitionRouteLocator
from ycyj_zhongtai.libs.exception.base import CommonException, CommonErrorCode
from ycyj_zhongtai.libs.log.log_ext import init_logger
from ycyj_zhongtai.libs.rpc.redis_rpc.base_worker import WorkerName
from ycyj_zhongtai.libs.zookeeper.client import ZookeeperMicroClient


"""
# 客户端调用对应的网关不需要指定版本，网关配置控制客户端使用哪个api版本 对应的service版本
# 客户端调用示例: http://app-gw.365ycyj.com:80/方法名?xx=aaa
# 升级规则：
从配置中心获取 接口对应的 队列名
根据版本找，如果没找到的找最大的版本号，只能向上升级
个别服务按最新版本号发布，已经部署的使用老版本号
网关版本需要配置最高版本号限制新服务接口
"""

class Gateway:

    def __init__(self, port: int = 80, service_name: str = WorkerName.AppGateWay):
        self.handlers = None
        self.port = port
        self.service_name = service_name

        self.default_router = None

    def set_argv(self, argv):
        # 设置参数
        logger.info('argv:{}'.format(argv))
        if len(argv) >= 2:
            self.port = argv[1]

        self.check_port()

    def check_port(self):
        if self.port == 0:
            raise CommonException(CommonErrorCode.PortNoSetting_Error)

    def start(self, argv):
        init_logger(self.service_name)
        self.set_argv(argv)
        application = tornado.web.Application(self.handlers)
        application.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


class AppGateway(Gateway):

    def __init__(self):
        super(AppGateway, self).__init__()
        self.discovery_client = ZookeeperDiscoveryClient(ZookeeperMicroClient(), root_path=ZookeeperMicroServicePath)
        self.route_definition_locator = DiscoveryClientRouteDefinitionLocator(self.discovery_client)
        self.route_locator = RouteDefinitionRouteLocator(route_def_locator=self.route_definition_locator)
        filters = [AuthGatewayFilter(), LoadBalancerClientFilter(),
                   RequestRateLimiterGatewayFilter(), ForwardRoutingFilter()]
        self.web_handler = FilteringWebHandler(filters=filters)
        self.handlers = [Rule(AnyMatches(), RequestForwardingHandler,
                              {'web_handler': self.web_handler, 'route_locator': self.route_locator})]


if __name__ == '__main__':
    AppGateway().start(sys.argv)
