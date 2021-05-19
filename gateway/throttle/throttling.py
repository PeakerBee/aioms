import time


from redis import Redis
from logger.log import gen_log

"""
GateWay 限流实现模块
"""
class BaseThrottle:
    """
       Rate throttling of requests.
       """

    def allow_request(self, key):
        """
        Return `True` if the request should be allowed, `False` otherwise.
        """
        raise NotImplementedError('.allow_request() must be overridden')

    def get_key(self, ident):
        pass

    def throttle_success(self) -> bool:
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        return True

    def throttle_failure(self) -> bool:
        """
        Called when a request to the API has failed due to throttling.
        """
        return False

    def wait(self):
        """
        Optionally, return a recommended number of seconds to wait before
        the next request.
        """
        return None


class TokenBucketThrottle(BaseThrottle):
    ReplenishRate = 30  # 令牌桶填充平均速率
    BurstCapacity = 200  # 令牌桶上限
    TokenReqPerTime = 1  # 每次消耗令牌数量，默认 1

    Lua = """
        local key = KEYS[1]
        
        local replenish_rate = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local req_token_num = tonumber(ARGV[3])
        local now_micros = tonumber(ARGV[4]) 

        local last_token_num = tonumber(redis.call("HGET",key,"token_num_key"))
        
        if (last_token_num == nil or type(last_token_num) == "boolean") then
            last_token_num = capacity
        end 
        
        
        local last_refresh_time = tonumber(redis.call("HGET",key,"last_timestamp_key"))
        
        if (last_refresh_time == nil or type(last_refresh_time) == "boolean") then
            last_refresh_time = 0
        end 
        
        local delta = math.max(0, now_micros - last_refresh_time)
        local replenish_num = (delta/1000) * replenish_rate
        local filled_token_num = math.min(capacity, last_token_num + replenish_num)
        
        local allowed = filled_token_num >= req_token_num
        local new_token_num = filled_token_num
        local allowed_num = 0
        if (allowed) then
            new_token_num = filled_token_num - req_token_num
            allowed_num = 1 
        end    

        redis.call("HSET",key,"token_num_key",new_token_num)
        redis.call("HSET",key,"last_timestamp_key",now_micros)
        
        redis.call("expire", key, 10)
        
        return {allowed_num, new_token_num, last_token_num, filled_token_num, delta, replenish_num}
    
    """

    def __init__(self, redis=Redis()):
        self.redis = redis

    def allow_request(self, key):

        if self.redis is None:
            return self.throttle_failure()
        cmd = self.redis.register_script(TokenBucketThrottle.Lua)
        timestamp = int(round(time.time() * 1000))
        result = cmd([key], [TokenBucketThrottle.ReplenishRate, TokenBucketThrottle.BurstCapacity, TokenBucketThrottle.TokenReqPerTime, timestamp])
        gen_log.debug(result)
        if len(result) > 0:
            if result[0] == 1:
                return self.throttle_success()



