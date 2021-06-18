# coding=utf-8
"""
@Time : 2021/6/18 9:01 
@Author : Peaker
some utility code method for mse
"""
import socket

local_ip = None


def get_local_ip():
    global local_ip
    if local_ip is None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        local_ip = ip
    return local_ip
