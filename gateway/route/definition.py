from enum import Enum

from discovery.instance import ServiceInstance
from exception.definition import CommonException
from exception.error_code import CommonErrorCode


class RpcType(Enum):
    HTTP = 1
    REDIS_RPC = 2


class RouteDefinition:
    def __init__(self, route_id: str, uri: str, route_type: 'RpcType' = RpcType.HTTP,
                 throttling=False, version='50000'):
        self.route_id = route_id
        self.uri = uri
        self.version = version
        self.route_type = route_type
        self.throttling = throttling


class Route:
    def __init__(self, route_id: str, uri: str, route_type: 'RpcType' = RpcType.HTTP,
                 throttling=False, version='50000'):
        self.route_id = route_id
        self.uri = uri
        self.version = version
        self.route_type = route_type
        self.throttling = throttling


class RedisRpcRouteDefinition(RouteDefinition):

    def __init__(self, route_id: str, uri: str, route_type: 'RpcType', password: 'str', user: 'str', version: 'str'):
        super(RedisRpcRouteDefinition).__init__(route_id=route_id, uri=uri, route_type=route_type, version=version)
        self.password = password
        self.user = user


class RouteFactory:

    @staticmethod
    def get_route(instance: 'ServiceInstance'):
        service_id = instance.get_service_id()
        version = instance.get_version()
        uri = f'{instance.get_host()}:{instance.get_port()}'
        route_type = RpcType.HTTP
        if instance.get_rpc_type() == RpcType.HTTP.value:
            return RouteDefinition(route_id=service_id, uri=uri, route_type=route_type, version=version)
        elif instance.get_rpc_type() == RpcType.REDIS_RPC.value:
            route_type = RpcType.REDIS_RPC
            uri = instance.get_meta_data().get('redis_host')
            pwd = instance.get_meta_data().get('password')
            user = instance.get_meta_data().get('user')
            return RedisRpcRouteDefinition(route_id=service_id, uri=uri, route_type=route_type,
                                           password=pwd, user=user, version=version)
        else:
            raise CommonException(error_code=CommonErrorCode.Rpc_Type_Error)
