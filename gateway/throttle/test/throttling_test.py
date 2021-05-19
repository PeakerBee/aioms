import threading
from time import sleep

from ycyj_zhongtai.gateway.throttle.throttling import TokenBucketThrottle










def run():
    throttle.allow_request("192.168.10.15:GetSMSCode")



if __name__ == '__main__':
    throttle = TokenBucketThrottle()
    while True:
        threading.Thread(target=run).start()

        #if s / 100 == 0:
        sleep(0.03)

