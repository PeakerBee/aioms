# coding=utf-8
import os
import sys

if __name__ == '__main__':
    root_dir = os.getcwd()
    print('sys.path.append({})'.format(root_dir))
    sys.path.append(root_dir)

version = "0.1.3"
