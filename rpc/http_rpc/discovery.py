import json
from typing import List, Dict

from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
from kazoo.recipe.watchers import ChildrenWatch

from discovery.event import WatchedEvent
from discovery.instance import ZookeeperServiceInstance, ServiceInstance
from discovery.service import ServiceDiscovery, DiscoveryClient
from gateway.discover import ZookeeperServiceCache


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
