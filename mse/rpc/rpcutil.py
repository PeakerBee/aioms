# coding=utf-8
"""
@Time : 2021/7/1 18:19 
@Author : Peaker
"""


class RpcServerRequest:
    pass


class RpcMessageDelegate:

    def data_received(self, chunk: 'bytes'):
        pass
