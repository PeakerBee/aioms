# coding=utf-8
import os
from logging import config
import yaml

log_config = yaml.load(open('{}/logging.yaml'.format(os.path.abspath(os.path.dirname(__file__))), 'r'), Loader=yaml.FullLoader)
config.dictConfig(log_config)
