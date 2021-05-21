import json

from discovery.service import ServiceProvider


class ZookeeperServiceRegistry(ServiceProvider):

    def __init__(self, zookeeper: 'KazooClient', root_path: str):
        self.zookeeper = zookeeper
        self.root_path = root_path

    def register_service(self, service: 'ServiceInstance') -> None:
        path = f'{self.root_path}/{service.get_service_id()}/{service.get_instance_id()}'
        service_data = json.dumps(service, default=lambda x: x.__dict__)
        self.zookeeper.set(path, service_data)

    def start(self) -> None:
        self.zookeeper.start()

    def stop(self) -> None:
        self.zookeeper.stop()


# class ServiceRegistry(ServiceProvider):
#
#     def __init__(self, default_registry: 'ServiceProvider') -> None:
#         if default_registry is None:
#             raise Exception()
#         self.default_registry = default_registry
#
#     def register_service(self, service: 'ServiceInstance') -> None:
#         self.default_registry.register_service(service)
#
#     def start(self) -> None:
#         self.default_registry.start()
