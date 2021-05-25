# coding=utf-8
"""
@author:yuceyingjia
@date:2020/12/09
"""
from rpc.prpc import rpc_proxy

if __name__ == '__main__':
    print(rpc_proxy.HQApi().F10_GaiNianTiCai(code='600000.SH'))

