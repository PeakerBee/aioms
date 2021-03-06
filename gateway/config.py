# coding=utf-8
"""
@Time : 2021/6/17 15:27 
@Author : Peaker
"""
import os

import yaml

from ctx.config import ENV_YAML_DIC, CURRENT_ENV, AbsConfigOption, \
    create_app_config, create_discovery_config, create_redis_config


class ConfigOption(AbsConfigOption):

    def __init__(self):
        super().__init__()
        env_name = ENV_YAML_DIC[CURRENT_ENV]
        curr_path = os.path.dirname(__file__)
        env_yaml_path = os.path.join(f'{curr_path}/static', env_name)
        self.config_dic = yaml.load(open(env_yaml_path, encoding='utf-8'), Loader=yaml.FullLoader)
        self.configure()

    def configure(self):
        config_dic = self.config_dic
        app_config_info = config_dic.get('application', None)
        self.app_config = create_app_config(app_config_info)
        self.discovery_config = create_discovery_config(app_config_info)
        self.redis_config = create_redis_config(app_config_info)

