# coding=utf-8
"""
@Time : 2021/6/17 16:40 
@Author : Peaker
"""
from typing import Any

from ctx.config import DiscoveryConfig
from discovery.service import ServiceProvider
from micro.registry import ZookeeperServiceRegistry
from zookeeper.client import ZookeeperMicroClient


class AbsFactory:

    def apply(self, conf: 'Any'):
        raise NotImplementedError()


class ServiceRegistryFactory(AbsFactory):

    def apply(self, conf: 'DiscoveryConfig') -> 'ServiceProvider':
        """
        Service Registry Class responsible for creating ServiceProvider according to the config
        """

        if conf.name == 'zookeeper':
            service_provider = ZookeeperServiceRegistry(zookeeper=ZookeeperMicroClient(hosts=conf.url),
                                                        root_path=conf.root_path)
            return service_provider
