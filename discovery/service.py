from typing import List

from ycyj_zhongtai.libs.discovery.event import WatchedEvent
from ycyj_zhongtai.libs.discovery.instance import ServiceInstance


class DiscoveryClient:

    def get_instances(self, service_id: str) -> List[ServiceInstance]:
        raise NotImplementedError()

    def get_services(self) -> List[str]:
        raise NotImplementedError()

    def add_watch(self, watch: 'WatchedEvent'):
        raise NotImplementedError()


class ServiceDiscovery:

    def start(self) -> None:
        pass

    def query_for_instances(self, name: str) -> List['ServiceInstance']:
        pass

    def query_for_instances_by_id(self, name: str, service_id: str) -> 'ServiceInstance':
        pass

    def query_for_names(self) -> List[str]:
        pass

    def stop(self) -> None:
        pass

    def add_watch(self, watch: 'WatchedEvent'):
        raise NotImplementedError()


class ServiceProvider:

    def start(self) -> None:
        pass

    def register_service(self, service: 'ServiceInstance') -> None:
        pass

    def stop(self) -> None:
        pass
