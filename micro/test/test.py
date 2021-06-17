from tornado.web import RequestHandler

from micro.service import Application


def index():
    return 'test'


if __name__ == "__main__":
    handlers = [
        (r"/", RequestHandler, {'func': index}),
    ]

    application = Application(handlers=handlers, name="User", root_path='/micro-service', port=803)
    application.start()
