# -*- coding: utf-8 -*-

import json
import uuid
from loguru import logger
from ycyj_zhongtai.libs.rpc.http_rpc.rpc import rpc_proxy as http_rpc_proxy, ClusterRpcProxy
from ycyj_zhongtai.libs.rpc.redis_rpc.redis import Redis
from ycyj_zhongtai.libs.rpc.redis_rpc.exceptions import NoRedisCreatedError, MethodFormatError


class RpcClient:
    def __init__(self, redis=Redis(), base_key=None):
        self.redis = redis
        self.base_key = base_key

    def random_key(self):
        new_key = str(uuid.uuid4())

        if self.base_key is None:
            return new_key
        else:
            return "{},{}".format(self.base_key, new_key)

    def send_request(self, resp, queue_name, method, *params, **kwargs):
        id = self.random_key()
        if not params:
            params = None
        params_val = params
        if kwargs is not None and kwargs != {}:
            params_val = kwargs

        request = {'id': id,
                   'queue_name': queue_name,
                   'method': method,
                   'params': params_val}

        logger.debug('request = {}'.format(request))
        if resp is not None and 'sw6' in resp:
            request['sw6'] = resp['sw6']
        self.redis.lpush(queue_name, json.dumps(request))
        # 只要有调用，就会顺延时间，如果时间不过期历史的会保留
        # 不考虑后端处理超时情况
        self.redis.expire(queue_name, 15)
        return id

    def get_response(self, id, timeout=15):
        channel, response = self.redis.brpop(id, timeout)  # 如果超时会抛异常
        return response.decode('utf-8')


class RpcClientProxy(RpcClient):

    def request(self, method, *params, **kwargs) -> str:
        """
         微服务之间进行调用的的方法，调用规则类似于http 接口访问
        :param method: /worker_name/version_code/method
        :param params: 请求的参数
        :param kwargs:
        :return:
        """

        if self.redis is None:
            logger.info('redis don‘t be created')
            raise NoRedisCreatedError('redis don‘t be none')

        methods = method.split('/')[1:]

        if len(methods) < 3:
            raise MethodFormatError('请求方法格式错误！！{}'.format(method))

        queue_name = 'work:{}:{}'.format(methods[0], methods[1])

        request_method = methods[2]

        id = self.send_request(None, queue_name, request_method, *params, **kwargs)
        jstr = self.get_response(id, timeout=15)
        # logger.info(jstr)
        return jstr


class HttpRpcClient:
    def __init__(self):
        self.rpc_proxy = http_rpc_proxy  # type: [ClusterRpcProxy]
