from ycyj_zhongtai import WorkerName
from ycyj_zhongtai.libs.api_handler import ApiHandler
from ycyj_zhongtai.libs.micro.web import Application


def index():
    return 'test'


if __name__ == "__main__":
    handlers = [
        (r"/", ApiHandler, {'func': index}),
    ]

    application = Application(handlers=handlers, name=WorkerName.YCYJGongShiApi, root_path='/micro-service', port=803)
    application.start()
