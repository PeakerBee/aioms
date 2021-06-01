# coding=utf-8
"""
@Time : 2021/6/1 10:19 
@Author : Peaker
@Function: Factory class
"""
from typing import Any

from gateway.config import DiscoveryConfig
from zookeeper.client import ZookeeperMicroClient
from zookeeper.discovery import ZookeeperDiscoveryClient


class AbsFactory:

    def apply(self, conf: 'Any'):
        raise NotImplementedError()


class DiscoveryFactory(AbsFactory):

    def apply(self, conf: 'DiscoveryConfig') -> 'DiscoveryClient':
        """
        Discovery Factory Class responsible for creating DiscoveryClient according to the config
        """

        if conf.name == 'zookeeper':
            discovery_client = ZookeeperDiscoveryClient(ZookeeperMicroClient(hosts=conf.url), root_path=conf.root_path)
            return discovery_client
