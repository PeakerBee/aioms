# coding=utf-8
"""
@Time : 2021/5/25 14:17 
@Author : Peaker
@rpc: mse rpc by http
"""
from tornado.httpclient import HTTPClient

from rpc.route import RouteDefinition


def request(route: 'RouteDefinition', method_name: 'str', **kwargs) -> str:

    params_val = ''
    if kwargs is not None and kwargs != {}:
        for key, value in kwargs.items():
            params_val = f'{key}={value}&'

    if params_val and params_val != '':
        params_val = params_val[:-1]
        params_val = f'?{params_val}'

    host = route.uri
    real_request_url = f'http://{host}/{method_name}{params_val}'
    http_client = HTTPClient()
    response = http_client.fetch(request=real_request_url)
    return str(response.body)
