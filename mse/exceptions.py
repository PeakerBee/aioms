# coding=utf-8
"""
@Time : 2021/5/20 10:28 
@Author : Peaker
"""
from exception.definition import AbsException
from exception.error_code import MseErrorCode


class ServiceRegistryError(AbsException):

    def __init__(self, error_code=MseErrorCode.Service_Registry_Error):
        super(ServiceRegistryError, self).__init__(error_code=error_code)


class ConfigNotSettingError(AbsException):
    def __init__(self, error_code=MseErrorCode.Config_Not_Setting_Error):
        super(ConfigNotSettingError, self).__init__(error_code=error_code)
