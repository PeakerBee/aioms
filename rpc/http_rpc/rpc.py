# coding=utf-8
import functools
import threading
from typing import List

from tornado.httpclient import HTTPClient
from ycyj_zhongtai.gateway.app.loadbalancer import RandomRule
from ycyj_zhongtai.libs.discovery.event import ServiceWatchedEvent
from ycyj_zhongtai.libs.discovery.instance import ServiceInstance
from ycyj_zhongtai.libs.discovery.service import DiscoveryClient
from ycyj_zhongtai.libs.rpc.http_rpc.discovery import ZookeeperDiscoveryClient
from ycyj_zhongtai.libs.zookeeper.client import ZookeeperMicroClient


class RouteDefinition:
    def __init__(self, route_id: str, uri: str):
        self.route_id = route_id
        self.uri = uri


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
        service_id = instance.get_service_id()
        uri = f'{instance.get_host()}:{instance.get_port()}'
        route_definition = RouteDefinition(route_id=service_id, uri=uri)
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


class ClusterRpcProxy(object):
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
        params_val = ''
        if kwargs is not None and kwargs != {}:
            for key, value in kwargs.items():
                params_val = f'{key}={value}&'

        if params_val and params_val != '':
            params_val = params_val[:-1]
            params_val = f'?{params_val}'

        lookup_route = functools.partial(self.look_up_route, self.service_name)
        routes = list(filter(lookup_route, self._ctx.get_route_definitions()))
        route = self.load_balancer_rule.choose(routes)

        if not route:
            raise Exception()

        host = route.uri
        real_request_url = f'http://{host}/{self.method_name}{params_val}'
        http_client = HTTPClient()
        response = http_client.fetch(request=real_request_url)
        return response.body

    def look_up_route(self, service_name: str, route: 'RouteDefinition'):
        return service_name == route.route_id


rpc_proxy = ClusterRpcProxy()
