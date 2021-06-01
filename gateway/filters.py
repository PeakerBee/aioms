import asyncio
import base64
import gzip
import json
import urllib
import uuid

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.httputil import HTTPHeaders
from tornado.web import HTTPError

from gateway.app import Gateway
from gateway.context import ApplicationContext
from gateway.exceptions import RpcTypeError, ThrottleError, ApiNotFoundException
from gateway.loadbalancer import RandomRule
from gateway.filter.definition import GatewayFilter, GatewayFilterChain
from gateway.route.definition import RpcType
from gateway.throttle.throttling import TokenBucketThrottle
from gateway.web import GATEWAY_REQUEST_ROUTE_ATTR, REQUEST_METHOD_NAME, GATEWAY_ROUTE_ATTR, MICRO_SERVICE_NAME, \
    ServerWebExchange
from rpc.redis import RedisClient


class ForwardRoutingFilter(GatewayFilter):

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        route = exchange.get_attributes(GATEWAY_REQUEST_ROUTE_ATTR)
        if route.rpc_type == RpcType.HTTP:
            http_routing_filter = HttpRoutingFilter()
            http_routing_filter.filter(exchange=exchange, chain=chain)
            chain.filter(exchange)
        elif route.rpc_type == RpcType.REDIS_RPC:
            rpc_route_filter = RpcRoutingFilter()
            rpc_route_filter.filter(exchange=exchange, chain=chain)
            chain.filter(exchange)
        else:
            raise RpcTypeError()


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
            origin_header = request.get_origin_header().get_all()
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
        route = exchange.get_attributes(GATEWAY_REQUEST_ROUTE_ATTR)
        host = route.uri
        redis = RedisClient(host=host, password=route.password, username=route.user)
        service_name = exchange.get_attributes(MICRO_SERVICE_NAME)
        method_name = exchange.get_attributes(REQUEST_METHOD_NAME)
        version = route.version
        queue_name = 'work:{}:{}'.format(service_name, version)

        request = exchange.get_request()
        headers = request.get_header()
        arg_dic = {}
        # 支持Post Json格式
        if 'Content-Type' in headers and headers['Content-Type'] == 'application/json':
            if headers.get('Content-Encoding') == 'gzip' and isinstance(request.get_body(), bytes):
                body = gzip.decompress(request.get_body()).decode('utf-8')
            post_json_dic = json.loads(body)  # post 发送的json对象字典
            for key in post_json_dic:
                arg_dic[key.lower()] = post_json_dic[key]
        elif 'Content-Type' in headers and headers['Content-Type'].__contains__('xml'):
            http_body = request.get_body()
            xml = http_body.decode('utf-8')
            import xmltodict
            xml_dict = xmltodict.parse(xml)
            for key in xml_dict:
                arg_dic[key.lower()] = xml_dict[key]

        for key in request.get_files():
            for file in request.get_files()[key]:
                file['body'] = base64.b64encode(file['body']).decode('utf-8')
            arg_dic[key.lower()] = request.get_files()[key]

        query = request.get_query()

        if query:
            p_arr = query.split(r'&')
            for p_str in p_arr:
                s_arr = p_str.split(r'=')
                arg_dic[s_arr[0].lower()] = urllib.parse.unquote(s_arr[1])

        header_param = request.get_header()

        if header_param:
            for key, value in header_param:
                arg_dic[key.lower()] = urllib.parse.unquote(value)

        request = {'id': str(uuid.uuid4()),
                   'queue_name': queue_name,
                   'method': method_name,
                   'params': arg_dic}

        redis.lpush(queue_name, json.dumps(request))
        redis.expire(queue_name, 15)
        channel, response = redis.brpop(id, 15)  # 如果超时会抛异常
        return response.decode('utf-8')


class LoadBalancerClientFilter(GatewayFilter):

    def __init__(self):
        self.load_balancer_rule = RandomRule()

    def filter(self, exchange: 'ServerWebExchange', chain: 'GatewayFilterChain'):
        route = self.load_balancer_rule.choose(exchange.get_attributes(GATEWAY_ROUTE_ATTR))

        # if route is None:
        #     raise ApiNotFoundException(exchange.get_attributes(MICRO_SERVICE_NAME))

        exchange.set_attributes(GATEWAY_REQUEST_ROUTE_ATTR, route)
        chain.filter(exchange)


class RequestRateLimiterGatewayFilter(GatewayFilter):

    def __init__(self, context: 'ApplicationContext'):
        host = context.get_redis_config().host
        password = context.get_redis_config().password
        redis = RedisClient(host=host, password=password)
        self.throttling = TokenBucketThrottle(redis=redis)

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
