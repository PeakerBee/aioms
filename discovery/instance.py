from typing import Dict, List


class ServiceInstance(object):

    def get_instance_id(self) -> str:
        """
        :return: The unique instance ID as registered
        """

        raise NotImplementedError()

    def get_service_id(self) -> str:
        """
        :return: The service ID as registered.
        """

        raise NotImplementedError()

    def get_host(self) -> str:
        """
        :return: The port of the registered service instance.
        """

        raise NotImplementedError()

    def get_port(self) -> int:
        """
        :return: The port of the registered service instance.
        """

        raise NotImplementedError()

    def get_version(self) -> str:
        """
        :return: The Micro Service Version
        """
        raise NotImplementedError()

    def get_meta_data(self) -> Dict[str, str]:
        """
        :return: The key / value pair metadata associated with the service instance.
        """

        raise NotImplementedError()


class ServiceCache(object):

    def get_instances(self) -> List[ServiceInstance]:
        pass

    def set_instances(self, instances: List[ServiceInstance]) -> None:
        pass

    def get_name(self) -> str:
        """
        :return: The name of the micro service.
        """
        raise NotImplementedError()

    def destroy(self) -> None:
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def set_watch(self, watch: 'ChildrenWatch'):
        raise NotImplementedError()


class DefaultServiceInstance(ServiceInstance):

    def __init__(self, instance_id: str, service_id: str, host: str, port: int, metadata: Dict[str, str]):
        self.instance_id = instance_id
        self.service_id = service_id
        self.host = host
        self.port = port
        self.metadata = metadata

    def get_instance_id(self):
        return self.instance_id

    def get_service_id(self):
        return self.service_id

    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def get_meta_data(self):
        return self.metadata

    def get_version(self) -> str:
        pass


class ZookeeperServiceInstance(ServiceInstance):

    def __init__(self, instance_id: str, service_id: str, host: str, port: int, version: int = 50000,
                 metadata: Dict[str, str] = None):
        self.instance_id = instance_id
        self.service_id = service_id
        self.host = host
        self.port = port
        self.version = version
        self.metadata = metadata

    def get_instance_id(self) -> str:
        return self.instance_id

    def get_service_id(self) -> str:
        return self.service_id

    def get_host(self) -> str:
        return self.host

    def get_port(self) -> int:
        return self.port

    def get_meta_data(self) -> Dict[str, str]:
        return self.metadata

    def get_version(self) -> str:
        pass
