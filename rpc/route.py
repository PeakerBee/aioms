# coding=utf-8
"""
@Time : 2021/5/25 14:29 
@Author : Peaker
"""
from enum import Enum

from discovery.instance import ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode


class RpcType(Enum):
    HTTP = 1
    REDIS_RPC = 2


class RouteDefinition:
    def __init__(self, route_id: str, uri: str, rpc_type: 'RpcType', version='v1'):
        self.route_id = route_id
        self.uri = uri
        self.rpc_type = rpc_type
        self.version = version


class RedisRpcRouteDefinition(RouteDefinition):

    def __init__(self, route_id: str, uri: str, rpc_type: 'RpcType', password: 'str', user: 'str'):
        super(RedisRpcRouteDefinition).__init__(route_id, uri, rpc_type)
        self.password = password
        self.user = user


class RouteFactory:

    @staticmethod
    def get_route(instance: 'ServiceInstance'):
        service_id = instance.get_service_id()
        uri = f'{instance.get_host()}:{instance.get_port()}'
        if instance.get_rpc_type() == RpcType.HTTP.value:
            return RouteDefinition(route_id=service_id, uri=uri, rpc_type=instance.get_rpc_type())
        elif instance.get_rpc_type() == RpcType.REDIS_RPC.value:
            pwd = instance.get_meta_data().get('password')
            user = instance.get_meta_data().get('user')
            return RedisRpcRouteDefinition(route_id=service_id, uri=uri, rpc_type=instance.get_rpc_type(),
                                           password=pwd, user=user)
        else:
            raise CommonException(error_code=CommonErrorCode.Rpc_Type_Error)
