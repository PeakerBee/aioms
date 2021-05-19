# coding=utf-8
"""
@author:yuceyingjia
@date:2020/09/07
"""
from ycyj_zhongtai.libs.exception.base import YCYJBaseException, AppGWErrorCode


class AppGWException(YCYJBaseException):

    def __init__(self, error_code=AppGWErrorCode.General_Error):
        super(AppGWException, self).__init__(error_code)


class RouteTypeError(AppGWException):
    def __init__(self, error_code=AppGWErrorCode.Route_Type_Error):
        super(AppGWException, self).__init__(error_code)


class ThrottleError(AppGWException):
    def __init__(self, error_code=AppGWErrorCode.Throttle_Error):
        super(AppGWException, self).__init__(error_code)


class VersionNumTooTowError(AppGWException):
    def __init__(self, api_name=None):
        super(AppGWException, self).__init__(error_code=AppGWErrorCode.Version_Num_Too_Low_Error)
        if api_name:
            self.msg = '{} 接口版本号太低'.format(api_name)


class VersionFormatError(AppGWException):
    def __init__(self, error_code=AppGWErrorCode.Version_Format_Error):
        super(AppGWException, self).__init__(error_code)


class AccessTokenCheckError(AppGWException):
    def __init__(self, msg=None):
        super(AccessTokenCheckError, self).__init__(AppGWErrorCode.Access_Token_Error)
        if msg:
            self.msg = msg


class WorkerTimeoutError(AppGWException):
    def __init__(self, msg=None):
        super(WorkerTimeoutError, self).__init__(AppGWErrorCode.Worker_Timeout_Error)
        if msg:
            self.msg = msg
