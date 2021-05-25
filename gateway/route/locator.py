import threading
from typing import List

from discovery.event import ServiceWatchedEvent
from gateway.route.definition import RouteDefinition, Route


class RouteLocator:

    def get_routes(self) -> List['Route']:
        raise NotImplementedError()

    def convert_to_route(self, route_instance: 'RouteDefinition'):
        raise NotImplementedError()


class RouteDefinitionLocator:

    def get_route_definitions(self) -> List[RouteDefinition]:
        raise NotImplementedError()


class RouteDefinitionRouteLocator(RouteLocator):

    def __init__(self, route_def_locator: 'RouteDefinitionLocator'):
        self.route_definition_locator = route_def_locator

    def get_routes(self) -> List['Route']:
        return list(map(self.convert_to_route, self.route_definition_locator.get_route_definitions()))

    def convert_to_route(self, route_instance: 'RouteDefinition') -> Route:
        return Route(route_id=route_instance.route_id, uri=route_instance.uri, route_type=route_instance.route_type)


class DiscoveryClientRouteDefinitionLocator(RouteDefinitionLocator):

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

        watcher = ServiceWatchedEvent(func=self.service_watch_event)
        self.discovery_client.add_watch(watcher)

    def service_watch_event(self):
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

    def _create_route_definition(self, instance: 'ServiceInstance'):
        service_id = instance.get_service_id()
        uri = f'{instance.get_host()}:{instance.get_port()}'
        route_definition = RouteDefinition(route_id=service_id, uri=uri)
        return route_definition
