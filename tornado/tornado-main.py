#!/usr/bin/env python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "derbysite.settings")
os.environ.setdefault("PYTHONPATH", ".")
import logging.config

import django  # Jan2014: Added for 1.7

from tornado.options import options, define
import django.core.handlers.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.websocket

from derbysite.settings import LOGGING

logging.config.dictConfig(LOGGING)
log = logging.getLogger('tornado')
define('port', type=int, default=8080)
tornado.options.parse_command_line()

clients = {}


def ohash(x):
    return hash(x)


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def data_received(self, chunk):
        log.warning('Stub: data_received doing nothing.')
        pass

    def open(self, *args):
        log.info('WebSocketHandler: open')
        id = ohash(self)  # self.get_argument("id")
        self.stream.set_nodelay(True)
        clients[id] = self
        log.info('WebSocketHandler: added new client, id:{}'.format(id))

    def on_message(self, message):
        log.info('Received message from client [%s]: [%s]' % (ohash(self), message))
        if message == 'Peekaboo!':
            for key in clients:
                socket = clients[key]
                #                 if socket == self:
                #                     continue
                log.info('Sending msg to client id={}'.format(key))
                socket.write_message('The chicken has fled the crib.')

    def on_close(self):
        id = ohash(self)
        if id in clients:
            del clients[id]
            log.info('Tornado removed client, id:{}'.format(id))


def main():
    wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
    CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

    static_path = os.path.join(CURRENT_PATH, '../hosted-static/')
    print('static_path = {}'.format(static_path))
    favicon_path = static_path

    handlers = [
        (r'/(favicon.ico)', tornado.web.StaticFileHandler, {'path': static_path}),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
        (r'/socket/refresh/', WebSocketHandler),
        (r'.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
    ]

    tornado_app = tornado.web.Application(handlers)
    django.setup()  # Jan2014: Added for 1.7
    log.info("Tornado starting")
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
