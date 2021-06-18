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


将错误码统一放到一起，没有放到各个模块是为了好维护，为了让大家知道那些错误码已经被使用
若是后续业务复杂了，就需要放到各个模块进行违法，这样子代码冲突就会少很多
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
    NameNoSetting_Error = (200007, 'GateWay', 'Service Name没有设置')
    Rpc_Type_Error = (200008, 'GateWay', '路由类型错误')
    Discovery_Conf_Not_Setting_Error = (200009, 'GateWay', '服务发现配置没有设置')
    Rpc_Conf_Not_Setting_Error = (200010, 'GateWay', 'Rpc方式没有进行配置')
    Redis_Conf_Not_Setting_Error = (200011, 'GateWay', 'Redis没有进行配置')


class GWErrorCode(ErrorCode):
    """App GateWay Error Code"""
    General_Error = (201001, 'GateWay', '通用错误')
    Channel_Absent = (201002, 'GateWay', '没有可用的通道')
    Param_Absent = (201003, 'GateWay', '参数缺失')
    Access_Token_Error = (201004, 'GateWay', 'AccessToken鉴权失败')
    Api_Timeout_Error = (201005, 'GateWay', '接口请求超时')
    Version_Format_Error = (201006, 'GateWay', '接口版本号格式错误')
    Version_Num_Too_Low_Error = (201007, 'GateWay', '接口版本号太低')
    Throttle_Error = (201008, 'GateWay', '访问高峰期...')
    Discovery_Not_Setting_Error = (201009, 'GateWay', '服务发现没有配置')


class RPCErrorCode(ErrorCode):
    General_Error = (202001, 'RPC', '通用错误')
    Service_Not_Found_Error = (202002, 'RPC', '服务没有发现')


class MseErrorCode(ErrorCode):
    General_Error = (203001, 'Mse', '通用错误')
    Service_Registry_Error = (203002, 'Mse', '服务注册没有创建')
    Config_Not_Setting_Error = (203003, 'Mse', '配置文件没有设置')
