# coding=utf-8
"""
@Time : 2021/6/18 10:12 
@Author : Peaker
"""
import uuid

from discovery.instance import ServiceInstance
from mse.httpserver import Application, RouteType
from mse.utils import get_local_ip
from zookeeper.discovery import ZookeeperServiceInstance


class RpcServer(Application):





    def create_service_instance(self) -> 'ServiceInstance':
        instance_id = str(uuid.uuid4())
        service_id = self.service_name
        host = get_local_ip()
        port = self.port
        metadata = dict()
        metadata['redis_host'] = self.context.get_redis_config().host
        metadata['password'] = self.context.get_redis_config().password
        metadata['user'] = self.context.get_redis_config().user
        service = ZookeeperServiceInstance(instance_id=instance_id, service_id=service_id,
                                           host=host, port=port,
                                           version=self.version,
                                           rpc_type=RouteType.REDIS_RPC.value,
                                           metadata=metadata)

        return service
