# coding=utf-8

from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError, NodeExistsError

from logger.log import gen_log

"""
Custom ZookeeperClient by extend KazooClient
"""


class ZookeeperMicroClient(KazooClient):
    """
       ZooKeeper服务注册客户端
       """

    def __init__(self, hosts: str):
        super(ZookeeperMicroClient, self).__init__(hosts=hosts)

    def set(self, path, value, version=-1):

        """
        设置指定路径的值
        多线程同时创建路径时会产生 NodeExistsError 异常
        """

        if not self.exists(path):
            try:
                self.create(path, value.encode('utf-8'), makepath=True, ephemeral=False)
            except NodeExistsError as ex:
                gen_log.info(ex)
        else:
            super(ZookeeperMicroClient, self).set(path, value.encode('utf-8'))

    def get(self, path, watch=None):
        try:
            val = super(ZookeeperMicroClient, self).get(path)
            if val is None:
                return ''
            return val[0].decode('utf-8')
        except NoNodeError as ex:
            gen_log.info(ex)

    def get_children(self, path, watch=None, include_data=False):
        try:
            ls = super(ZookeeperMicroClient, self).get_children(path, watch, include_data)
            if ls is None:
                return []
            return ls
        except NoNodeError as ex:
            gen_log.info(ex)
            return []
