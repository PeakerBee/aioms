# coding=utf-8
"""
GateWay Web Server Config
"""
import sys
from typing import Dict

from env.definition import ENV_DEV, ENV_TEST, ENV_PROD, ENV_BETA
from exception.definition import CommonException
from exception.error_code import CommonErrorCode

CURRENT_ENV = ENV_TEST

ENV_YAML_DIC = {ENV_DEV: 'app-dev.yaml',
                ENV_TEST: 'app-test.yaml',
                ENV_BETA: 'app-beta.yaml',
                ENV_PROD: 'app-prod.yaml'}

for v in sys.argv:
    if str(v).lower() == ENV_PROD:
        CURRENT_ENV = ENV_PROD
    elif str(v).lower() == ENV_BETA:
        CURRENT_ENV = ENV_BETA
    elif str(v).lower() == ENV_TEST:
        CURRENT_ENV = ENV_TEST
    else:
        CURRENT_ENV = ENV_DEV


def create_app_config(config_info: 'Dict'):
    return AppConfig(config_info)


def create_discovery_config(config_info: 'Dict'):
    return DiscoveryConfig(config_info)


def create_redis_config(config_info: 'Dict'):
    return RedisConfig(config_info)


class AbsConfigOption:

    def __init__(self):
        self.discovery_config = None  # type: [DiscoveryConfig]
        self.app_config = None  # type: [AppConfig]
        self.redis_config = None  # type: [RedisConfig]

    def get_discovery_config(self) -> 'DiscoveryConfig':
        return self.discovery_config

    def get_redis_config(self) -> 'RedisConfig':
        return self.redis_config

    def get_name(self) -> str:
        if self.app_config:
            return self.app_config.name

    def get_port(self) -> int:
        if self.app_config:
            return self.app_config.port

    def get_version(self) -> int:
        if self.app_config:
            return self.app_config.version

    def configure(self) -> None:
        raise NotImplementedError()


class Config:

    def config_parse(self, config_info: dict):
        raise NotImplementedError()


class AppConfig(Config):

    def __init__(self, config_info: 'Dict'):
        self.name = None
        self.port = 0
        self.version = 5000
        self.config_parse(config_info)

    def config_parse(self, config_info: 'Dict'):
        if config_info:
            self.name = config_info.get('name')
            self.port = config_info.get('port') or 0
            self.version = config_info.get('version') or 50000


class DiscoveryConfig(Config):

    def __init__(self, config_info: 'Dict'):
        self.name = None
        self.url = None
        self.root_path = None
        self.config_parse(config_info)

    def config_parse(self, config_info: dict):
        if config_info:
            discovery_config = config_info.get('discovery')
            if discovery_config:
                self.name = discovery_config.get('name', None)
                self.url = discovery_config.get('url', None)
                self.root_path = discovery_config.get('root_path', None)
                if self.name is None or self.url is None and self.root_path is None:
                    raise CommonException(error_code=CommonErrorCode.Discovery_Conf_Not_Setting_Error)
        else:
            raise CommonException(error_code=CommonErrorCode.Discovery_Conf_Not_Setting_Error)


class RedisConfig(Config):
    def __init__(self, config_info: dict):
        self.host = None
        self.user = None
        self.password = None
        self.config_parse(config_info)

    def config_parse(self, config_info: dict):
        if config_info:
            redis_config = config_info.get('redis')
            if redis_config:
                self.user = redis_config.get('user', None)
                self.host = redis_config.get('host', None)
                self.password = redis_config.get('password', None)

                if self.host is None:
                    raise CommonException(error_code=CommonErrorCode.Redis_Conf_Not_Setting_Error)
        else:
            raise CommonException(error_code=CommonErrorCode.Redis_Conf_Not_Setting_Error)
