# coding=utf-8
"""
@Time : 2021/6/1 9:54 
@Author : Peaker
@Function: GateWay App ctx
 Central interface to provide configuration for an application.
 ctx Env Info for an application
"""


class AbsAppContext:

    def get_app_name(self):
        raise NotImplementedError()

    def get_port(self):
        raise NotImplementedError()

    def get_env(self):
        raise NotImplementedError()

    def get_version(self):
        raise NotImplementedError()


class ConfApplicationContext(AbsAppContext):

    def get_discovery_config(self):
        raise NotImplementedError()

    def get_redis_config(self):
        raise NotImplementedError()
