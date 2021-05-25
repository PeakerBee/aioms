import asyncio

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.httputil import HTTPHeaders
from tornado.web import HTTPError

from gateway.exceptions import RouteTypeError, ThrottleError, ApiNotFoundException
from gateway.loadbalancer import RandomRule
from gateway.filter.definition import GatewayFilter, GatewayFilterChain
from gateway.route.definition import RouteType
from gateway.throttle.throttling import TokenBucketThrottle
from gateway.web import GATEWAY_REQUEST_ROUTE_ATTR, REQUEST_METHOD_NAME, GATEWAY_ROUTE_ATTR, MICRO_SERVICE_NAME, \
    ServerWebExchange
from rpc.redis_rpc.redis import RedisClient


class ForwardRoutingFilter(GatewayFilter):

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        route = exchange.get_attributes(GATEWAY_REQUEST_ROUTE_ATTR)
        if route.route_type == RouteType.HTTP:
            http_routing_filter = HttpRoutingFilter()
            http_routing_filter.filter(exchange=exchange, chain=chain)
            chain.filter(exchange)
        elif route.route_type == RouteType.REDIS_RPC:
            rpc_route_filter = RpcRoutingFilter()
            rpc_route_filter.filter(exchange=exchange, chain=chain)
            chain.filter(exchange)
        else:
            raise RouteTypeError()


class HttpRoutingFilter(GatewayFilter):

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        asyncio.run(self.http_request(exchange, chain))

    async def http_request(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):

        try:
            route = exchange.get_attributes(GATEWAY_REQUEST_ROUTE_ATTR)
            method_name = exchange.get_attributes(REQUEST_METHOD_NAME)
            host = route.uri
            request = exchange.get_request()
            query = request.get_query()
            origin_header = request.get_header().get_all()
            header = HTTPHeaders()
            for key, value in origin_header:
                if key != 'Host' and key != 'If Modified Since ':
                    header.add(key, value)
            real_request_url = f'http://{host}/{method_name}?{query}'
            # real_request_url = 'https://app-gw-test.365ycyj.com/HQApi/50000/GetStockJianPinList?ts=4d5459794d4459354e5467304f513d3d'
            http_client = AsyncHTTPClient()
            method = exchange.get_request().get_method_name()
            http_request = HTTPRequest(url=real_request_url, method=method.upper())
            response = await http_client.fetch(request=http_request, headers=header)
            exchange.get_response().set_response_body(str(response.body))
            chain.filter(exchange)
        except Exception as ex:
            if isinstance(ex, HTTPClientError):
                raise HTTPError(code=ex.code, reason=ex.__str__())
            else:
                raise HTTPError(code=500, reason=ex.__str__())


class RpcRoutingFilter(GatewayFilter):

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        pass


class LoadBalancerClientFilter(GatewayFilter):

    def __init__(self):
        self.load_balancer_rule = RandomRule()

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        route = self.load_balancer_rule.choose(exchange.get_attributes(GATEWAY_ROUTE_ATTR))

        if route is None:
            raise ApiNotFoundException(exchange.get_attributes(MICRO_SERVICE_NAME))

        exchange.set_attributes(GATEWAY_REQUEST_ROUTE_ATTR, route)
        chain.filter(exchange)


class RequestRateLimiterGatewayFilter(GatewayFilter):

    def __init__(self):
        self.throttling = TokenBucketThrottle(RedisClient())

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        route = exchange.get_attributes(GATEWAY_REQUEST_ROUTE_ATTR)
        if route and route.throttling:
            remote_ip = exchange.get_request().get_remote_ip()
            service_name = exchange.get_attributes(MICRO_SERVICE_NAME)
            method_name = exchange.get_attributes(REQUEST_METHOD_NAME)
            key = f'{remote_ip}:{service_name}:{method_name}'
            if not self.throttling.allow_request(key):
                raise ThrottleError()

        chain.filter(exchange)


class AuthGatewayFilter(GatewayFilter):

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        chain.filter(exchange)
