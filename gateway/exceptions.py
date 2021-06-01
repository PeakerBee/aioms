# coding=utf-8
"""
@author:yuceyingjia
@date:2020/09/07
"""
from exception.definition import AbsException
from exception.error_code import GWErrorCode, CommonErrorCode


class GWException(AbsException):

    def __init__(self, error_code=GWErrorCode.General_Error):
        super(GWException, self).__init__(error_code)


class DiscoveryNotSettingError(GWException):
    
    def __init__(self, error_code=GWErrorCode.Discovery_Not_Setting_Error):
        super(DiscoveryNotSettingError, self).__init__(error_code=error_code)
        

class ApiNotFoundException(GWException):
    def __init__(self, api_name=''):
        super(ApiNotFoundException, self).__init__(error_code=CommonErrorCode.ApiNotFound_Error)
        self.msg = '{} 接口不存在'.format(api_name)

    def __str__(self):
        return self.msg


class RpcTypeError(GWException):
    def __init__(self, error_code=CommonErrorCode.Rpc_Type_Error):
        super(GWException, self).__init__(error_code)


class ThrottleError(GWException):
    def __init__(self, error_code=GWErrorCode.Throttle_Error):
        super(GWException, self).__init__(error_code)


class VersionNumTooTowError(GWException):
    def __init__(self, api_name=None):
        super(GWException, self).__init__(error_code=GWErrorCode.Version_Num_Too_Low_Error)
        if api_name:
            self.msg = '{} 接口版本号太低'.format(api_name)


class VersionFormatError(GWException):
    def __init__(self, error_code=GWErrorCode.Version_Format_Error):
        super(GWException, self).__init__(error_code)


class ApiFormatErrorException(GWException):
    def __init__(self, api_name=''):
        super(ApiFormatErrorException, self).__init__(error_code=CommonErrorCode.ApiFormat_Error)
        self.msg = '{} 接口格式不正确'.format(api_name)

    def __str__(self):
        return self.msg


class AccessTokenCheckError(GWException):
    def __init__(self, msg=None):
        super(AccessTokenCheckError, self).__init__(GWErrorCode.Access_Token_Error)
        if msg:
            self.msg = msg


class ApiTimeoutError(GWException):
    def __init__(self, msg=None):
        super(ApiTimeoutError, self).__init__(GWErrorCode.Api_Timeout_Error)
        if msg:
            self.msg = msg
