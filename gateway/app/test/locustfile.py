# coding=utf-8

from locust import HttpLocust, TaskSet, task


class WebsiteTasks(TaskSet):

    # def on_start(self):
    #     self.client.post("/login", {
    #         "username": "test_user",
    #         "password": ""
    #     })
    @task
    def LongHuBangAllXiWei(self):
        self.client.get(
            "/GongShiApi/50000/LongHuBangAllXiWei")
    # @task
    # def GetPankouDataList2(self):
    #     self.client.get(
    #         "/UserApi/50000/LoginByPassword?tel=17631662414&password=888888&systemVersion=Windows10&loginType=0")
    #

class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks

    min_wait = 5000
    max_wait = 15000
    # http://114.215.177.91/UserApi/50000/LoginByPassword
    # http://pc-gw.365ycyj.com/UserApi/50000/LoginByPassword?tel=17631662414&password=888888&systemVersion=Windows10&loginType=0
    # 终端运行：locust -f locustfile.py --host=http://pc-gw.365ycyj.com
    # 终端运行：locust -f locustfile.py --host=http://app-gw-test.365ycyj.com
    # 终端运行：locust -f locustfile.py --host=http://127.0.0.1:20081
    # 终端运行：locust -f locustfile.py --host=http://114.215.177.91
    # 运行结果：http://localhost:8089
