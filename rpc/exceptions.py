# coding=utf-8
"""
@Time : 2021/5/25 14:44 
@Author : Peaker
"""
from exception.definition import AbsException
from exception.error_code import RPCErrorCode


class MSNotFoundError(AbsException):
    """
    micro service not found
    """
    def __init__(self, service_name=''):
        super(MSNotFoundError, self).__init__(error_code=RPCErrorCode.Service_Not_Found_Error)
        self.msg = '{} 服务不存在'.format(service_name)

    def __str__(self):
        return self.msg
