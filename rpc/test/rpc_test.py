# coding=utf-8
"""
@author:yuceyingjia
@date:2020/12/09
"""
from rpc.prpc import ClusterRpcProxy

if __name__ == '__main__':
    rpc_proxy = ClusterRpcProxy()
    print(rpc_proxy.HQApi().F10_GaiNianTiCai(code='600000.SH'))

