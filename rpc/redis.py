# coding=utf-8
"""
@Time : 2021/5/25 14:18 
@Author : Peaker
@rpc: mse rpc by redis
"""
import json
import uuid

from redis import Redis

from rpc.route import RedisRpcRouteDefinition


class RedisClient(Redis):
    """
    Redis Client
    """


def request(route: 'RedisRpcRouteDefinition', service_name, method_name, **kwargs) -> str:
    host = route.uri
    redis = RedisClient(host=host, password=route.password, username=route.user)
    queue_name = 'work:{}:{}'.format(service_name, route.version)

    id = str(uuid.uuid4())

    params_val = None
    if kwargs is not None and kwargs != {}:
        params_val = kwargs

    request_info = {'id': id,
                    'queue_name': queue_name,
                    'method': method_name,
                    'params': params_val}

    redis.lpush(queue_name, json.dumps(request_info))
    redis.expire(queue_name, 15)
    channel, response = redis.brpop(id, 15)  # 如果超时会抛异常
    return response.decode('utf-8')
