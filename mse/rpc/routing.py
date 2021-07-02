# coding=utf-8
"""
@Time : 2021/7/1 18:16 
@Author : Peaker
Flexible routing implementation for rpc.
"""
from typing import Any

from mse.rpc.rpcutil import RpcServerRequest, RpcMessageDelegate


class RuleRouter:

    def find_handler(self, request: 'RpcServerRequest', **kwargs: Any) -> RpcMessageDelegate:
        pass

    def get_target_delegate(self) -> RpcMessageDelegate:
        pass
