import functools
import json
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List


from tornado.concurrent import run_on_executor
from tornado.web import RequestHandler, HTTPError

from gateway.context import ApplicationContext
from gateway.exceptions import VersionFormatError, ApiFormatErrorException, GWException
from gateway.filter.definition import GatewayFilterChain, GatewayFilter
from gateway.web import TornadoServerHttpRequest, DefaultServerWebExchange, TornadoServerHttpResponse, \
    MICRO_SERVICE_NAME, REQUEST_METHOD_NAME, MICRO_SERVICE_VERSION, GATEWAY_ROUTE_ATTR, ServerWebExchange, APP_CONTEXT
from logger.log import gen_log


class RequestForwardingHandler(RequestHandler):
    """Gateway Network request forwarding Handler
    Forward http request to target Micro Server
    This implementation extends ~.RequestHandler
    """

    # default thread pool
    executor = ThreadPoolExecutor(500)

    def initialize(self, web_handler: 'WebHandler', route_locator: 'RouteLocator') -> None:
        self.web_handler = web_handler
        self.route_locator = route_locator

    @run_on_executor()
    def handle_request(self):
        try:

            server_http_request = TornadoServerHttpRequest(self.request)
            server_http_response = TornadoServerHttpResponse(self)
            server_web_exchange = DefaultServerWebExchange(server_http_request, server_http_response)
            path = self.request.path[1:]
            method_names = path.split('/')
            if len(method_names) > 2:
                service_name = method_names[0]
                method_name = method_names[2]
                try:
                    # check service version format, must be digital
                    version = int(method_names[1])
                except ValueError:
                    raise VersionFormatError()
            else:
                raise ApiFormatErrorException(path)

            server_web_exchange.set_attributes(MICRO_SERVICE_NAME, service_name)
            server_web_exchange.set_attributes(REQUEST_METHOD_NAME, method_name)
            server_web_exchange.set_attributes(MICRO_SERVICE_VERSION, version)
            lookup_route = functools.partial(self.lookup_route, server_web_exchange)
            routes = list(filter(lookup_route, self.route_locator.get_routes()))
            server_web_exchange.set_attributes(GATEWAY_ROUTE_ATTR, routes)
            self.web_handler.handle(server_web_exchange)
            return server_http_response.get_response_body()
        except Exception as ex:
            if isinstance(ex, GWException):
                state_val = ex.state
            elif isinstance(ex, HTTPError):
                raise ex
            else:
                state_val = 0
            r_dict = {'State': state_val, 'Msg': str(ex), 'Data': ''}
            if state_val == 0:
                gen_log.exception(ex)  # 只有未知异常才记录，其他异常记录警告日志
            else:
                gen_log.warning(ex)

            r_str = json.dumps(r_dict, ensure_ascii=False)
            return r_str

    async def get(self):
        res = await self.handle_request()
        await self.finish(res)

    async def post(self):
        res = await self.handle_request()
        await self.finish(res)

    async def head(self):
        await self.finish('GateWay')

    async def options(self):
        """
        前端页面进行跨域访问需要实现options方法，否则无法进行跨域访问
        """
        pass

    def set_default_headers(self):
        """
        设置跨域
        :return:
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        # 这里要填写上请求带过来的Access-Control-Allow-Headers参数，如 WG-App-Version 就是我请求带过来的参数
        self.set_header("Access-Control-Allow-Headers",
                        "Origin, X-Requested-With, Content-Type, Accept, WG-App-Version, \
                        WG-Device-Id, WG-Network-Type, WG-Vendor, WG-OS-Type, WG-OS-Version, \
                        WG-Device-Model, WG-CPU, WG-Sid, WG-App-Id, WG-Token, Token, AppType, User-html-Agent")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")  # 请求允许的方法
        self.set_header("Access-Control-Max-Age", "3600")  # 用来指定本次预检请求的有效期，单位为秒，在此期间不用发出另一条预检请求。
        # 定义一个响应OPTIONS 请求，不用作任务处理

    def lookup_route(self, server_web_exchange: 'ServerWebExchange', route: 'Route'):
        return server_web_exchange.get_attributes(MICRO_SERVICE_NAME) == route.route_id


class WebHandler:
    def handle(self, server_web_exchange: 'ServerWebExchange'):
        raise NotImplementedError()


class FilteringWebHandler(WebHandler):

    def __init__(self, filters: List['GatewayFilter']):
        self.filters = filters

    def handle(self, server_web_exchange: 'ServerWebExchange'):
        chain = DefaultGatewayFilterChain(self.filters)
        chain.filter(server_web_exchange)


class DefaultGatewayFilterChain(GatewayFilterChain):

    def __init__(self, filters: List['GatewayFilter'], index: int = 0):
        self.filters = filters
        self.index = index

    def get_filters(self) -> List['GatewayFilter']:
        return self.filters

    def filter(self, exchange: 'ServerWebExchange'):
        if self.index < len(self.filters):
            filter_handler = self.filters[self.index]
            chain = DefaultGatewayFilterChain(self.get_filters(), self.index + 1)
            return filter_handler.filter(exchange, chain)
