# coding=utf-8
"""
@Time : 2021/6/1 9:54 
@Author : Peaker
@Function: GateWay App Context
 Central interface to provide configuration for an application.
 Context Env Info for an application
"""
from gateway.config import ConfigOption, CURRENT_ENV, DiscoveryConfig, RpcConfig, RedisConfig


class AbstractApplicationContext:

    def get_app_name(self):
        raise NotImplementedError()

    def get_port(self):
        raise NotImplementedError()

    def get_env(self):
        raise NotImplementedError()


class ConfigApplicationContext(AbstractApplicationContext):

    def get_discovery_config(self):
        raise NotImplementedError()


class ApplicationContext(ConfigApplicationContext):

    def __init__(self):
        self.config_option = ConfigOption()

    def get_app_name(self) -> str:
        return self.config_option.get_name()

    def get_port(self) -> int:
        return self.config_option.get_port()

    def get_env(self) -> str:
        return CURRENT_ENV

    def get_discovery_config(self) -> 'DiscoveryConfig':
        return self.config_option.get_discovery_config()

    def get_redis_config(self) -> 'RedisConfig':
        return self.config_option.get_redis_config()


def create_app_context() -> 'ApplicationContext':
    return ApplicationContext()
