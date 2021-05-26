# coding=utf-8
"""
GateWay Web Server Config
"""
import os
import sys

import yaml

from env import ENV_PROD, ENV_TEST, ENV_BETA, ENV_DEV
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


class ConfigOption(dict):

    def __init__(self):
        super().__init__()
        env_name = ENV_YAML_DIC[CURRENT_ENV]
        curr_path = os.path.dirname(__file__)
        env_yaml_path = os.path.join(f'{curr_path}/static', env_name)
        self.discovery_config = None  # type: [DiscoveryConfig]
        self.app_config = None  # type: [AppConfig]
        self.server_config = None  # type: [ServerConfig]
        self.config_dic = yaml.load(open(env_yaml_path, encoding='utf-8'), Loader=yaml.FullLoader)
        self.configure()

    def configure(self):
        config_dic = self.config_dic
        server = config_dic.get('server', None)
        self.config_server(server)
        app = config_dic.get('application', None)
        self.config_app(app)
        self.config_discovery(app)

    def config_server(self, config_info: dict):
        if config_info:
            self.server_config = ServerConfig(port=config_info.get('port'))

    def config_app(self, config_info: dict):
        if config_info:
            self.app_config = AppConfig(name=config_info.get('name'))

    def config_discovery(self, config_info: dict):
        if config_info:
            discovery_config = config_info.get('discovery')
            if discovery_config:
                name = discovery_config.get('name', None)
                url = discovery_config.get('url', None)
                root_path = discovery_config.get('root_path', None)
                if name and url and root_path:
                    self.discovery_config = DiscoveryConfig(name=name, url=url, root_path=root_path)
                else:
                    raise CommonException(error_code=CommonErrorCode.Discovery_Conf_Not_Setting_Error)
        else:
            raise CommonException(error_code=CommonErrorCode.Discovery_Conf_Not_Setting_Error)

    def get_discovery_config(self):
        return self.discovery_config

    def get_name(self):
        if self.app_config:
            return self.app_config.name

    def get_server_port(self):
        if self.server_config:
            return self.server_config.port


class ServerConfig:

    def __init__(self, port: int):
        self.port = port


class AppConfig:

    def __init__(self, name: str):
        self.name = name


class DiscoveryConfig:

    def __init__(self, name: str, url: str, root_path: str):
        self.name = name
        self.url = url
        self.root_path = root_path


config = ConfigOption()
