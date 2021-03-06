# coding=utf-8
"""
@Time : 2021/6/17 16:05 
@Author : Peaker
"""
from ctx.config import CURRENT_ENV
from ctx.context import ConfApplicationContext
from gateway.config import ConfigOption


class ApplicationContext(ConfApplicationContext):

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
