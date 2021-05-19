# coding=utf-8
"""
@Time : 2021/5/19 16:31 
@Author : Peaker
"""
from exception.error_code import ErrorCode


class AbsException(Exception):
    def __init__(self, error_code: ErrorCode = None):
        if error_code:
            self.state = error_code.error_code
            self.msg = '{} {}'.format(error_code.module_name, error_code.des)
        else:
            self.state = 200000
            self.msg = ''

    def __str__(self):
        return self.msg


class CommonException(AbsException):
    def __init__(self, error_code: ErrorCode = None):
        if error_code:
            self.state = error_code.error_code
            self.msg = '{} {}'.format(error_code.module_name, error_code.des)
        else:
            self.state = 200000
            self.msg = ''

    def __str__(self):
        return self.msg
