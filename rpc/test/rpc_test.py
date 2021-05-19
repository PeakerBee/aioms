 # coding=utf-8
"""
@author:yuceyingjia
@date:2020/12/09
"""
from ycyj_zhongtai.libs.rpc.http_rpc.rpc import rpc_proxy

if __name__ == '__main__':
    print(rpc_proxy.HQApi().F10_GaiNianTiCai(code='600000.SH'))

