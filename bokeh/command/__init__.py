from __future__ import print_function

import argparse
import os
import time
import subprocess
import sys

from bokeh.settings import settings
from bokeh.server import start
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread

def die(message):
    print(message, file=sys.stderr)
    sys.exit(1)

class Subcommand(object):
    """Abstract base class for subcommands"""

    def __init__(self, parser):
        """Initialize the subcommand with its parser; can call parser.add_argument to add subcommand flags"""
        self.parser = parser

    def func(self, args):
        """Takes over main program flow to perform the subcommand"""
        pass

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server

    def on_any_event(self, event):
        #print("file event: " + repr(event))
        #print("event_type: " + event.event_type)
        #print("src_path: " + event.src_path)
        # TODO handle more kinds of file changing
        if event.event_type == "modified":
            self.server.file_modified(event.src_path)

class LocalServer(Subcommand):
    """Abstract base class for subcommands that launch a single-user local server"""

    def __init__(self, **kwargs):
        super(LocalServer, self).__init__(**kwargs)
        self.parser.add_argument('--port', metavar='PORT', type=int, help="Port to listen on", default=-1)
        self.port = 5006
        self.develop_mode = False

    def load(self, src_path):
        import ast
        from types import ModuleType
        source = open(src_path, 'r').read()
        nodes = ast.parse(source, src_path)
        code = compile(nodes, filename=src_path, mode='exec')
        module = ModuleType(self.appname)
        exec(code, module.__dict__)

    def refresh(self, open_browser):
        from bokeh.plotting import show, push
        from bokeh.io import curdoc

        curdoc().context.develop_shell.error_panel.visible = False
        curdoc().context.develop_shell.reloading.visible = True
        push()

        # TODO rather than clearing curdoc() we'd ideally
        # save the old one and compute a diff to send.
        # also we have a hack here to keep the old develop
        # shell ID :-/
        old_shell = curdoc().context.develop_shell
        curdoc().clear()
        curdoc().context.develop_shell = old_shell
        try:
            print("Loading %s" % self.docpy)
            self.load(self.docpy)
        except Exception as e:
            import traceback
            formatted = traceback.format_exc(e)
            print(formatted)
            curdoc().context.develop_shell.error_panel.error = formatted
            curdoc().context.develop_shell.error_panel.visible = True

        curdoc().context.develop_shell.reloading.visible = False
        if open_browser:
            show(curdoc())
        else:
            push()
        print("Done loading %s" % self.docpy)

    def file_modified(self, path):
        # TODO rather than ignoring file changes in prod mode,
        # don't even watch for them
        if self.develop_mode and path == self.docpy:
            self.refresh(open_browser=False)

    # this is a cut-and-paste from bokeh.server in order to
    # start the main loop separately
    def listen_simple_server(self, port=-1, args=None):
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

    def background_simple_server(self):
        from tornado import ioloop
        ioloop.IOLoop.instance().start()

    def stop_simple_server(self):
        start.stop()

    def func(self, args):

        self.directory = os.getcwd()
        self.docpy = os.path.join(self.directory, "doc.py")

        if not os.path.exists(self.docpy):
            die("No 'doc.py' found in %s." % (self.directory))

        self.appname = os.path.basename(self.directory)

        if self.directory not in sys.path:
            print("adding %s to python path" % self.directory)
            sys.path.append(self.directory)

        if args.port >= 0:
            self.port = args.port
        if self.develop_mode:
            print("Starting %s in development mode on port %d" % (self.appname, self.port))
        else:
            print("Starting %s in production mode on port %d" % (self.appname, self.port))

        event_handler = FileChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, self.directory, recursive=True)
        observer.start()

        self.listen_simple_server(port=self.port)

        # this is probably pretty evil and not safe if there are any
        # globals shared between the bokeh server and client code,
        # which I think there are. The right fix may be to have an
        # alternative to output_server that works in-process?
        thread = Thread(target=self.background_simple_server)
        thread.start()

        # here we are connecting to ourselves, which is kind of
        # silly, we should be going in-process
        from bokeh.plotting import output_server
        output_server(self.appname)

        self.refresh(open_browser=True)

        try:
            # thread.join isn't actually interruptable
            # but leaving the keyboardinterrupt handler
            # for now since I want to replace the thread
            # stuff by avoiding the blocking output_server
            # call above.
            thread.join()
        except KeyboardInterrupt:
            self.stop_simple_server()
            observer.stop()
        observer.join()

class Develop(LocalServer):
    name = "develop"
    help = "Run a Bokeh server in developer mode"

    def __init__(self, **kwargs):
        super(Develop, self).__init__(**kwargs)
        self.develop_mode = True

class Run(LocalServer):
    name = "run"
    help = "Run a Bokeh server in production mode"

    def __init__(self, **kwargs):
        super(Run, self).__init__(**kwargs)

subcommands = [Develop, Run]

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0])
    # does this get set by anything other than BOKEH_VERSION env var?
    version = settings.version()
    if not version:
        version = "unknown version"
    parser.add_argument('-v', '--version', action='version', version=version)
    subs = parser.add_subparsers(help="Sub-commands")
    for klass in subcommands:
        c_parser = subs.add_parser(klass.name, help=klass.help)
        c = klass(parser=c_parser)
        c_parser.set_defaults(func=c.func)

    args = parser.parse_args(argv[1:])
    args.func(args)
