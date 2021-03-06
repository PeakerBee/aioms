# coding=utf-8
"""
@Time : 2021/5/25 13:28 
@Author : Peaker
"""
import collections
import typing
from http.cookies import Morsel, SimpleCookie
from typing import Dict, Union, Any, List, Iterator

from tornado.httputil import HTTPServerRequest, HTTPHeaders, HTTPFile
from tornado.web import RequestHandler

GATEWAY_ROUTE_ATTR = 'gatewayRoute'
GATEWAY_REQUEST_ROUTE_ATTR = 'targetGatewayRoute'
MICRO_SERVICE_NAME = 'microServiceName'
REQUEST_METHOD_NAME = 'methodName'
MICRO_SERVICE_VERSION = 'microServiceVersion'


class ServerWebExchange:

    def get_request(self) -> 'ServerHttpRequest':
        raise NotImplementedError()

    def get_response(self) -> 'ServerHttpResponse':
        raise NotImplementedError()

    def get_attributes(self, name: str) -> Any:
        raise NotImplementedError()

    def set_attributes(self, key: str, value: Any):
        raise NotImplementedError()


class ServerHTTPHeaders(dict):
    pass


class ServerHttpRequest:

    def get_path(self) -> str:
        raise NotImplementedError()

    def get_cookies(self):
        raise NotImplementedError()

    """get remote source ip address"""

    def get_remote_ip(self) -> str:
        raise NotImplementedError()

    def get_query(self):
        raise NotImplementedError()

    def get_body(self) -> str:
        raise NotImplementedError()

    def get_files(self) -> Any:
        raise NotImplementedError()

    """
    get http method type such as Get, Post, Head
    """

    def get_method_name(self):
        raise NotImplementedError()

    def get_origin_header(self) -> Any:
        raise NotImplementedError()

    def get_header(self) -> ServerHTTPHeaders:
        pass


class ServerHttpResponse:

    def get_status_code(self) -> int:
        raise NotImplementedError()

    def set_status_code(self, status_code: int):
        raise NotImplementedError()

    def get_cookies(self) -> SimpleCookie:
        raise NotImplementedError()

    def add_cookies(self, key, cookie):
        raise NotImplementedError()

    def get_response_body(self):
        raise NotImplementedError()

    def set_response_body(self, body: Union[str, bytes, dict]):
        raise NotImplementedError()


class DefaultServerWebExchange(ServerWebExchange):

    def __init__(self, server_http_request: 'ServerHttpRequest', server_http_response: 'ServerHttpResponse'):
        self.server_http_request = server_http_request
        self.server_http_response = server_http_response
        self.attributes = dict()

    def get_request(self):
        return self.server_http_request

    def get_response(self):
        return self.server_http_response

    def get_attributes(self, name: str):
        return self.attributes.get(name)

    def set_attributes(self, name: str, value: Any):
        self.attributes[name] = value


class TornadoServerHttpHeaders(ServerHTTPHeaders):
    pass


class TornadoServerHttpResponse(ServerHttpResponse):

    def __init__(self, request_handler: 'RequestHandler'):
        self.request_handler = request_handler
        self.response_body = None

    def get_response_body(self) -> Union[str, bytes, dict]:
        return self.response_body

    def set_response_body(self, body: Union[str, bytes, dict]):
        self.response_body = body

    def get_status_code(self) -> int:
        return self.request_handler.get_status()

    def set_status_code(self, status_code: int):
        self.request_handler.set_status(status_code=status_code)

    def get_cookies(self) -> Dict[str, Morsel]:
        return self.request_handler.cookies

    def add_cookies(self, key, cookie):
        self.request_handler.cookies[key] = cookie


class TornadoServerHttpRequest(ServerHttpRequest):

    def __init__(self, request: 'HTTPServerRequest'):
        self.http_request = request

    def get_remote_ip(self):
        remote_ip = self.http_request.headers.get('Remoteip')
        return remote_ip if remote_ip is not None else self.http_request.remote_ip

    def get_cookies(self):
        return self.http_request.cookies

    def get_path(self):
        return self.http_request.path

    def get_query(self):
        return self.http_request.query

    def get_origin_header(self) -> 'HTTPHeaders':
        return self.http_request.headers

    def get_header(self) -> 'ServerHTTPHeaders':

        origin_header = self.get_origin_header().get_all()
        header = TornadoServerHttpHeaders()
        for key, value in origin_header:
            if key != 'Host' and key != 'If Modified Since ':
                header[key] = value
        return header

    def get_body(self):
        return self.http_request.body

    def get_files(self) -> Dict[str, List["HTTPFile"]]:
        return self.http_request.files

    """
    get http method type such as Get, Post, Head
    """

    def get_method_name(self):
        return self.http_request.method
