# coding=utf-8
import functools
import threading
from typing import List

from discovery.event import ServiceWatchedEvent
from discovery.instance import ServiceInstance
from discovery.service import DiscoveryClient
from exception.definition import CommonException
from exception.error_code import CommonErrorCode
from gateway.loadbalancer import RandomRule
from rpc import http, redis
from rpc.exceptions import MSNotFoundError
from rpc.route import RouteDefinition, RpcType, RouteFactory
from zookeeper.client import ZookeeperMicroClient
from zookeeper.discovery import ZookeeperDiscoveryClient


class RpcContext(object):

    def __init__(self, discovery_client: 'DiscoveryClient'):
        self.discovery_client = discovery_client
        self.services = discovery_client.get_services()
        self.service_instances = list()  # type: List[ServiceInstance]
        self._run_lock = threading.Lock()
        for service in self.services:
            instances = discovery_client.get_instances(service)  # type: List[ServiceInstance]
            if instances:
                self.service_instances.extend(instances)

        self.route_definitions = list(map(self._create_route_definition, self.service_instances))

        watcher = ServiceWatchedEvent(func=self.service_watched_event)
        self.discovery_client.add_watch(watcher)

    def _create_route_definition(self, instance: 'ServiceInstance'):
        route_definition = RouteFactory.get_route(instance)
        return route_definition

    def service_watched_event(self):
        with self._run_lock:
            services = self.discovery_client.get_services()
            service_instances = list()  # type: List[ServiceInstance]

            for service in services:
                instances = self.discovery_client.get_instances(service)  # type: List[ServiceInstance]
                if instances:
                    service_instances.extend(instances)

            route_definitions = list(map(self._create_route_definition, service_instances))
            self.service_instances = service_instances
            self.route_definitions = route_definitions
            self.services = services

    def get_route_definitions(self) -> List[RouteDefinition]:
        with self._run_lock:
            return self.route_definitions


class _ClusterRpcProxy(object):
    def __init__(self):
        self._ctx = RpcContext(ZookeeperDiscoveryClient(ZookeeperMicroClient(), root_path='/micro-service'))
        self._proxies = dict()

    def __getattr__(self, name):
        if name not in self._proxies:
            self._proxies[name] = ServiceProxy(name, self._ctx)
        return self._proxies[name]


class ServiceProxy(object):
    def __init__(self, service_name: str = 'ServiceProxy', ctx: 'RpcContext' = None):
        self.service_name = service_name
        self._ctx = ctx

    def __getattr__(self, method_name):
        return MethodProxy(self.service_name, self.service_version, method_name, self._ctx)

    def __call__(self, *args, **kwargs):
        if args and len(args) > 0:
            self.service_version = args[0]
        else:
            self.service_version = None
        return self


class MethodProxy(object):
    def __init__(self, service_name: str, service_version: int, method_name: str, ctx: 'RpcContext'):
        self.service_name = service_name
        self.service_version = service_version
        self.method_name = method_name
        self._ctx = ctx
        self.load_balancer_rule = RandomRule()

    def __call__(self, *args, **kwargs):
        lookup_route = functools.partial(self.look_up_route, self.service_name)
        routes = list(filter(lookup_route, self._ctx.get_route_definitions()))
        route = self.load_balancer_rule.choose(routes)

        if not route:
            raise MSNotFoundError()

        if route.rpc_type == RpcType.HTTP:
            return http.request(route=route, method_name=self.method_name, kwargs=kwargs)
        elif route.route_type == RpcType.REDIS_RPC:
            return redis.request(route=route, service_name=self.service_name, method_name=self.method_name, kwargs=kwargs)
        else:
            raise CommonException(error_code=CommonErrorCode.Rpc_Type_Error)

    @staticmethod
    def look_up_route(service_name: str, route: 'RouteDefinition'):
        return service_name == route.route_id


rpc_proxy = _ClusterRpcProxy()
