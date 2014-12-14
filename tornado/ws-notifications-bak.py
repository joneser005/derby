import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)

clients = {}

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

class IndexHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers",
            "Content-Type, Depth, User-Agent, X-File-Size, X-Requested-With, X-Requested-By, If-Modified-Since, X-File-Name, Cache-Control")

    @tornado.web.asynchronous
    def get(self):
        self.write("Tornado is active, but you are doing it wrong!")
        self.finish()

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        self.id = self.get_argument("id")
        self.stream.set_nodelay(True)
        clients[self.id] = self
        print("Tornado added new client, id:{}".format(self.id))

    def on_message(self, message):        
        print("Received message from client [%s]: [%s]" % (self.id, message))
        if (message == 'Peekaboo!'):
            for key in clients:
                socket = clients[key]
                if socket == self:
                    continue
                print('Sending msg to client id={}'.format(key))
                socket.write_message('The chicken has fled the crib.')

    def on_close(self):
        if self.id in clients:
            del clients[self.id]
            print("Tornado removed client, id:{}".format(self.id))

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/refresh/', WebSocketHandler)
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()