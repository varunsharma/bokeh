from __future__ import print_function

from ..server import start
from threading import Thread


def monkey_init_bokeh(clientdoc):
    # we monkeypatch to remove the below line that assumes a request
    #request.bokeh_server_document = clientdoc
    clientdoc.autostore = False
    clientdoc.autoadd = False

from ..server.views import backbone
backbone.init_bokeh = monkey_init_bokeh

class Server(object):
    """Runs a server which displays an in-process document"""

    def __init__(self, **kwargs):
        self.docid = None

        self.port = 5006
        if 'port' in kwargs:
            self.port = kwargs['port']

        self._listen_simple_server(port=self.port)
        self.appname = 'bokeh-app'
        if 'appname' in kwargs:
            self.appname = kwargs['appname']

        # this is probably pretty evil and not safe if there are any
        # globals shared between the bokeh server and client code,
        # which I think there are. The right fix may be to have an
        # alternative to output_server that works in-process?
        self.thread = Thread(target=self._background_simple_server)
        self.thread.start()

        self._create_document()

    def document_link(self, doc):
        return "http://localhost:%d/bokeh/doc/%s/%s" % (self.port, self.docid, doc.context._id)

    def push(self, doc, dirty_only=True):
        """Push changes to the document to the client"""

        ## cut and paste from bokeh.server to avoid REST
        from ..server.models import docs
        from ..server.app import bokeh_app
        from ..server.serverbb import BokehServerTransaction
        from ..server.views.backbone import ws_update
        from .. import protocol

        doc._add_all()
        models = doc._models.values()

        if dirty_only:
            models = [x for x in models if getattr(x, '_dirty', False)]

        if len(models) < 1:
            return

        # TODO clearly serializing to json here is absurd
        json = protocol.serialize_json(doc.dump(*models))
        data = protocol.deserialize_json(json.decode('utf-8'))

        for model in models:
            model._dirty = False

        docid = self.docid
        server_doc = docs.Doc.load(bokeh_app.servermodel_storage, docid)
        print("loaded server doc %s" % docid)
        bokehuser = bokeh_app.current_user()
        temporary_docid = None #str(uuid.uuid4())
        t = BokehServerTransaction(
            bokehuser, server_doc, 'rw', temporary_docid=temporary_docid
        )
        t.load()
        clientdoc = t.clientdoc
        clientdoc.load(*data, events='none', dirty=True)
        t.save()
        ws_update(clientdoc, t.write_docid, t.changed)

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
        from ..server.settings import settings as server_settings
        from tornado.httpserver import HTTPServer
        from ..server.app import bokeh_app, app
        from ..server.configure import configure_flask, make_tornado_app, register_blueprint

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

    # cut-and-paste from bokeh.server to avoid going through REST
    def _create_document(self):
        from ..server.app import bokeh_app
        from ..server.views.main import _makedoc # naughty
        from ..server.models import docs
        from ..server.serverbb import BokehServerTransaction
        from ..io import curdoc
        from .. import protocol

        user = bokeh_app.current_user()
        existing = filter(lambda x: x['title'] == self.appname, user.docs)
        if len(existing) > 0:
            self.docid = existing[0]['docid']
            print("Using existing doc %s id %s" % (self.appname, self.docid))
        else:
            doc = _makedoc(bokeh_app.servermodel_storage, user, self.appname)
            self.docid = doc.docid
            print("Made new doc %s id %s" % (self.appname, self.docid))

        docid = self.docid
        server_doc = docs.Doc.load(bokeh_app.servermodel_storage, docid)
        print("on create server doc %s" % docid)
        temporary_docid = None #str(uuid.uuid4())
        t = BokehServerTransaction(
            user, server_doc, 'rw', temporary_docid=None,
        )
        t.load()
        clientdoc = t.clientdoc
        all_models = clientdoc._models.values()
        # TODO clearly serializing to json here is absurd
        json = protocol.serialize_json(clientdoc.dump(*all_models))
        attrs = protocol.deserialize_json(json.decode('utf-8'))
        curdoc().merge(attrs)
