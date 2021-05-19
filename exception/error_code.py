# coding=utf-8
"""
@Time : 2021/5/19 14:24 
@Author : Peaker
"""
from enum import Enum

"""
# 错误码定义

成功 SUCCESS(0)

错误码 格式如下：
A-BB-CCC
A:错误级别，如1代表系统级错误，2代表服务级错误；
B:项目或模块名称，一般公司不会超过99个项目；
C:具体错误编号，自增即可，一个项目999种错误应该够用；

错误代码说明
如(20502)
2: 服务级错误（1为系统级错误）
 05: 服务模块代码
02: 具体错误代码
**B:模块名称，一般的公司一个系统不会超过99个模块所以暂时定两位；
**C:具体错误编号
      001 通用错误
      002 接口不存在

"""


class ErrorCode(Enum):
    def __init__(self, error_code, module_name, des):
        """
         Common base class for all custom error code
        :param error_code:
        :param module_name: 所属模块
        :param des: 错误码对应的文字描述
        """
        self.error_code = error_code
        self.des = des
        self.module_name = module_name

    def describe(self):
        return '{} {} = {}'.format(self.module_name, self.des, self.error_code)


class CommonErrorCode(ErrorCode):
    ApiNotFound_Error = (200003, 'GateWay', 'Api接口不存在')
    ApiFormat_Error = (200004, 'GateWay', '接口格式不正确')
    PortNoSetting_Error = (200005, 'GateWay', 'PORT没有设置')
    HandlerNoSetting_Error = (200006, 'GateWay', 'Handler没有设置')
    NameNoSetting_Error = (200006, 'GateWay', 'Service Name没有设置')


class GWErrorCode(ErrorCode):
    """App GateWay Error Code"""
    General_Error = (201001, 'GateWay', '通用错误')
    Channel_Absent = (201002, 'GateWay', '没有可用的通道')
    Param_Absent = (201003, 'GateWay', '参数缺失')
    Access_Token_Error = (201004, 'GateWay', 'AccessToken鉴权失败')
    Api_Timeout_Error = (201005, 'GateWay', '接口请求超时')
    Version_Format_Error = (201006, 'GateWay', '接口版本号格式错误')
    Version_Num_Too_Low_Error = (201007, 'GateWay', '接口版本号太低')
    Route_Type_Error = (201008, 'GateWay', '路由类型错误')
    Throttle_Error = (201009, 'GateWay', '访问高峰期...')
