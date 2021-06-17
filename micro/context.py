# coding=utf-8
"""
@Time : 2021/6/17 16:07 
@Author : Peaker
"""
from ctx.config import CURRENT_ENV, DiscoveryConfig, RedisConfig
from ctx.context import ConfApplicationContext
from micro.config import ConfigOption


class ApplicationContext(ConfApplicationContext):

    def __init__(self, config_path: 'str'):
        self.config_option = ConfigOption(config_path)

    def get_app_name(self) -> str:
        return self.config_option.get_name()

    def get_port(self) -> int:
        return self.config_option.get_port()

    def get_version(self) -> int:
        return self.config_option.get_version()

    def get_env(self) -> str:
        return CURRENT_ENV

    def get_discovery_config(self) -> 'DiscoveryConfig':
        return self.config_option.get_discovery_config()

    def get_redis_config(self) -> 'RedisConfig':
        return self.config_option.get_redis_config()


def create_app_context(config_path: 'str') -> 'ApplicationContext':
    return ApplicationContext(config_path)
