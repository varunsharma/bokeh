from __future__ import print_function

import argparse
import os
import time
import subprocess
import sys

from bokeh.settings import settings
#import bokeh.server.start
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

    # TODO this is a hack for the time being;
    # we want to be the server, not spawn it.
    def start_background_server(self):
        # TODO fix path to bokeh-server
        self.bokehserver = subprocess.Popen(["./bokeh-server", "--port", str(self.port)])
        time.sleep(2) # wait for it to start up. HACK

        # TODO rather than publishing to separate server,
        # make changes in the current server
        from bokeh.plotting import output_server
        output_server(self.appname)

    def stop_background_server(self):
        self.bokehserver.terminate()
        time.sleep(1)
        self.bokehserver.kill()

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

        self.start_background_server()

        event_handler = FileChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, self.directory, recursive=True)
        observer.start()

        self.refresh(open_browser=True)

        try:
            # TODO this is if we were starting our own server
            #start.start_simple_server()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        #start.stop()
        self.stop_background_server()

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
