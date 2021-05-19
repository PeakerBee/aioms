import json
import threading

from typing import Dict, List
from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
from kazoo.client import ChildrenWatch

from discovery.event import WatchedEvent, ServiceWatchedEvent
from discovery.instance import ServiceCache, ServiceInstance, ZookeeperServiceInstance
from discovery.service import ServiceDiscovery, DiscoveryClient
from gateway.route.definition import RouteDefinition
from gateway.route.locator import RouteDefinitionLocator


class ZookeeperServiceCache(ServiceCache):

    def __init__(self, name: str):
        self._name = name
        self.watch = None  # type: [ChildrenWatch]
        self.instances = None

    def get_instances(self) -> List[ServiceInstance]:
        return self.instances

    def set_instances(self, instances: List[ServiceInstance]) -> None:
        self.instances = instances

    def get_name(self) -> str:
        return self._name

    def destroy(self):
        if self.watch:
            self.watch._stopped = True

    def clear(self):
        self.instances = None

    def set_watch(self, watch: 'ChildrenWatch'):
        self.watch = watch


class ZookeeperServiceDiscovery(ServiceDiscovery):

    def __init__(self, zookeeper: 'KazooClient', root_path: str):
        self.zookeeper = zookeeper
        self.service_nodes = dict()  # type:Dict[str, ZookeeperServiceCache]
        self.watches = set()  # type: [WatchedEvent]
        self.root_path = root_path

    def start(self) -> None:
        self.start_service_watch()

    def start_service_watch(self):
        self.zookeeper.start()
        ChildrenWatch(client=self.zookeeper, path=self.root_path, func=self._service_node_change)

    def _service_node_change(self, nodes: List[str]):
        old_nodes = [service for service in self.service_nodes.keys()]
        invalid_nodes = list(set(old_nodes).difference(set(nodes)))
        new_nodes = list(set(nodes).difference(set(old_nodes)))
        for node in invalid_nodes:
            self.remove_service_instance(node)
        for node in new_nodes:
            self.create_service_instance(node)

        for watch in self.watches:
            if callable(watch.func):
                watch.func()

    def remove_service_instance(self, service_id: str):
        service_cache = self.service_nodes.pop(service_id, None)
        if service_cache is not None:
            service_cache.destroy()

    def create_service_instance(self, service_id: str) -> None:
        node_path = f'{self.root_path}/{service_id}'
        service_cache = ZookeeperServiceCache(name=service_id)
        if self.service_nodes.get(service_id) is not None:
            self.service_nodes.pop(service_id).destroy()
        self.service_nodes[service_id] = service_cache

        def child_node_change(nodes: List[str]) -> None:
            if nodes is not None and len(nodes) > 0:
                service_instances = list()
                for node in nodes:
                    instance_path = f'{node_path}/{node}'
                    instance_data = self.zookeeper.get(instance_path)
                    service_instance = json.loads(str(instance_data))
                    instance_id = service_instance.get('instance_id')
                    service_name = service_instance.get('service_id')
                    host = service_instance.get('host')
                    port = service_instance.get('port')
                    version = service_instance.get('version')
                    service_instance = ZookeeperServiceInstance(service_id=service_name, instance_id=instance_id,
                                                                host=host, port=port, version=version)
                    service_instances.append(service_instance)

                service = self.service_nodes.get(service_id)
                if service is not None:
                    service.set_instances(service_instances)
            else:
                service = self.service_nodes.get(service_id)
                if service is not None:
                    service.clear()

            for watcher in self.watches:
                if callable(watcher.func):
                    watcher.func()

        watch = ChildrenWatch(client=self.zookeeper, path=node_path, func=child_node_change)
        service_cache.set_watch(watch)

    def query_for_instances(self, name: str) -> List['ServiceInstance']:
        instances = self.service_nodes.get(name).get_instances()
        return instances

    def query_for_names(self) -> List[str]:
        return list(self.service_nodes.keys())

    def stop(self):
        current_nodes = [service for service in self.service_nodes.keys()]
        list(map(self.remove_service_instance, current_nodes))

    def add_watch(self, watch: 'WatchedEvent'):
        self.watches.add(watch)


class ZookeeperDiscoveryClient(DiscoveryClient):

    def __init__(self, zookeeper: 'KazooClient', root_path: str):
        zookeeper.add_listener(self.connection_state_listener)
        self.service_discovery = ZookeeperServiceDiscovery(zookeeper, root_path)
        self.service_discovery.start()

    def connection_state_listener(self, state: str) -> None:
        if state == KazooState.LOST:
            self.service_discovery.stop()
            self.service_discovery.start()

    def add_watch(self, watch: 'WatchedEvent'):
        self.service_discovery.add_watch(watch)

    def get_instances(self, service_id: str) -> List[ServiceInstance]:
        return self.service_discovery.query_for_instances(service_id)

    def get_services(self) -> List[str]:
        return self.service_discovery.query_for_names()


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
