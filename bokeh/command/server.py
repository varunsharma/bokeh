from __future__ import print_function

from bokeh.server import start
from threading import Thread


class Server(object):
    """Runs a server which displays an in-process document"""

    def __init__(self, **kwargs):
        self.port = 5006
        if 'port' in kwargs:
            self.port = kwargs['port']

        self._listen_simple_server(port=self.port)

        # this is probably pretty evil and not safe if there are any
        # globals shared between the bokeh server and client code,
        # which I think there are. The right fix may be to have an
        # alternative to output_server that works in-process?
        self.thread = Thread(target=self._background_simple_server)
        self.thread.start()

        # here we are connecting to ourselves, which is kind of
        # silly, we should be going in-process
        from bokeh.plotting import output_server
        output_server('bokeh-develop') # nonsense app name

    def show(self, doc):
        """Push the document and then open it in a browser"""
        from bokeh.plotting import show
        show(obj=doc)

    def push(self, doc):
        """Push changes to the document to the client"""
        from bokeh.plotting import push
        push(document=doc)

    def waitFor(self):
        """Block until server shuts down"""
        # thread.join isn't actually interruptable
        # which currently prevents ctrl-C and is annoying
        self.thread.join()

    def stop(self):
        """Shut down the server"""
        self._stop_simple_server()

    # this is a cut-and-paste from bokeh.server in order to
    # start the main loop separately
    def _listen_simple_server(self, port=-1, args=None):
        from bokeh.server.settings import settings as server_settings
        from tornado.httpserver import HTTPServer
        from bokeh.server.app import bokeh_app, app
        from bokeh.server.configure import configure_flask, make_tornado_app, register_blueprint

        configure_flask(config_argparse=args)
        if server_settings.model_backend.get('start-redis', False):
            start.start_redis()
        register_blueprint()
        start.tornado_app = make_tornado_app(flask_app=app)
        start.server = HTTPServer(start.tornado_app)
        if port < 0:
            port = server_settings.port
        start.server.listen(port, server_settings.ip)

    def _background_simple_server(self):
        from tornado import ioloop
        ioloop.IOLoop.instance().start()

    def _stop_simple_server(self):
        start.stop()
