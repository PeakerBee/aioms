# coding=utf-8
"""
@author:yuceyingjia
@date:2020/11/27
"""
from redis import Redis
from ycyj_zhongtai.config.config_manage import ConfigManage


class YCYJRedisClient(Redis):
    def __init__(self):
        redis_config_obj = ConfigManage.get_val('ServiceWorker_Redis')
        super(YCYJRedisClient, self).__init__(host=redis_config_obj['host'],
                                              password=redis_config_obj['password'],
                                              retry_on_timeout=True)
