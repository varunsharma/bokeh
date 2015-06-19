from __future__ import print_function

import argparse
from bokeh.settings import settings

class Subcommand(object):
    """Abstract base class for subcommands"""

    def __init__(self, parser):
        """Initialize the subcommand with its parser; can call parser.add_argument to add subcommand flags"""
        self.parser = parser

    def func(self, args):
        """Takes over main program flow to perform the subcommand"""
        pass

class LocalServer(Subcommand):
    """Abstract base class for subcommands that launch a single-user local server"""

    def __init__(self, **kwargs):
        super(LocalServer, self).__init__(**kwargs)
        self.parser.add_argument('--port', metavar='PORT', type=int, help="Port to listen on", default=-1)

class Develop(LocalServer):
    name = "develop"
    help = "Run a Bokeh server in developer mode"

    def __init__(self, **kwargs):
        super(Develop, self).__init__(**kwargs)

    def func(self, args):
        # TODO make this do a real thing
        print("Develop! port %d" % (args.port))

class Run(LocalServer):
    name = "run"
    help = "Run a Bokeh server in production mode"

    def __init__(self, **kwargs):
        super(Run, self).__init__(**kwargs)

    def func(self, args):
        # TODO make this do a real thing
        print("Run! port %d" % (args.port))

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
