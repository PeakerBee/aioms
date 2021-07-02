# coding=utf-8
"""
@Time : 2021/7/1 18:19 
@Author : Peaker
"""


class RpcServerRequest:

    def __init__(self, return_id: 'str' = None, method: 'str' = None, **kwargs: 'any'):
        self.return_id = return_id
        self.method = method
        self.kwargs = kwargs


class RpcMessageDelegate:

    def execute(self):
        raise NotImplementedError()
