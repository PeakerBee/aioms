# coding=utf-8
from loguru import logger
from ycyj_zhongtai.config import YCYJ_CURRENT_ENV, YCYJ_ENV_DEV, YCYJ_ENV_TEST
from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError, NodeExistsError
from ycyj_zhongtai.config.config_manage import ConfigManage

"""
Custom ZookeeperClient by extend KazooClient
"""


class ZooKeeperClient(KazooClient):
    """
    ZooKeeper 配置客户端
    """

    def __init__(self, env=None):
        if env is not None:
            self.env = env
        else:
            self.env = YCYJ_CURRENT_ENV.lower()
        hosts_val = ConfigManage.get_val('ZooKeeperClientHost')
        super(ZooKeeperClient, self).__init__(hosts=hosts_val)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        self.stop()

    def set_val(self, path, val, ephemeral=False):
        """
        设置指定路径的值
        多线程同时创建路径时会产生 NodeExistsError 异常
        """
        if self.env == YCYJ_ENV_DEV:
            path = '/' + YCYJ_ENV_TEST + path
        else:
            path = '/' + self.env + path
        if not self.exists(path):
            self.create(path, val.encode('utf-8'), makepath=True, ephemeral=ephemeral)
        else:
            self.set(path, val.encode('utf-8'))

    def get_val(self, path):
        try:
            if self.env == YCYJ_ENV_DEV:
                path = '/' + YCYJ_ENV_TEST + path
                val = self.get(path)
                if val is None:
                    return ''
                return val[0].decode('utf-8')
            else:
                path = '/' + self.env + path
                val = self.get(path)
                if val is None:
                    return ''
                return val[0].decode('utf-8')
        except NoNodeError as ex:
            raise Exception('get_val(),NoNodeError, path:{}'.format(path))

    def get_children_ls(self, path):
        try:

            if self.env == YCYJ_ENV_DEV:
                path = '/' + YCYJ_ENV_TEST + path
                ls = self.get_children(path)
                if ls is None:
                    return []
                return ls
            else:
                path = '/' + self.env + path
                ls = self.get_children(path)
                if ls is None:
                    return []
                return ls
        except NoNodeError as ex:
            return []


class ZookeeperMicroClient(KazooClient):
    """
       ZooKeeper服务注册客户端
       """

    def __init__(self, env=None):
        if env is not None:
            self.env = env
        else:
            self.env = YCYJ_CURRENT_ENV.lower()
        hosts_val = ConfigManage.get_val('ZooKeeperClientHost')
        super(ZookeeperMicroClient, self).__init__(hosts=hosts_val)

    def set(self, path, value, version=-1):

        """
        设置指定路径的值
        多线程同时创建路径时会产生 NodeExistsError 异常
        """
        if self.env == YCYJ_ENV_DEV:
            path = '/' + YCYJ_ENV_TEST + path
        else:
            path = '/' + self.env + path
        if not self.exists(path):
            try:
                self.create(path, value.encode('utf-8'), makepath=True, ephemeral=False)
            except NodeExistsError as ex:
                logger.info(ex)
        else:
            super(ZookeeperMicroClient, self).set(path, value.encode('utf-8'))

    def get(self, path, watch=None):
        try:
            if self.env == YCYJ_ENV_DEV:
                path = '/' + YCYJ_ENV_TEST + path
            else:
                path = '/' + self.env + path

            val = super(ZookeeperMicroClient, self).get(path)
            if val is None:
                return ''
            return val[0].decode('utf-8')
        except NoNodeError as ex:
            logger.info(ex)

    def get_children(self, path, watch=None, include_data=False):
        try:

            if self.env == YCYJ_ENV_DEV:
                path = '/' + YCYJ_ENV_TEST + path
            else:
                path = '/' + self.env + path

            ls = super(ZookeeperMicroClient, self).get_children(path, watch, include_data)
            if ls is None:
                return []
            return ls
        except NoNodeError as ex:
            logger.info(ex)
            return []
