from os.path import relpath, splitext, basename, join, dirname, exists
from urllib.parse import urljoin
from collections import namedtuple
from django.template import TemplateSyntaxError
from django.http import HttpRequest
from ssr.settings import ENTRIES_DIR, BUNDLES_DIR, CACHE_DIR, SOCKETS_DIR
from ssr.server import Server


class Template:
    Env = namedtuple('Env', [
        'entry',
        'out_file',
        'out_dir',
        'script_relpath',
        'socket',
        'cache_dir'
    ])

    def __init__(self, path: str, root: str, production_mode: bool,
                 server: Server, server_script: str, client_script: str,
                 build_hash: str, static_url: str, dist_dir: str) -> None:
        self.render_server = server
        self.relpath = relpath(path, root)

        root_relpath = splitext(self.relpath)[0]
        socket_relpath = root_relpath + '-bundler.sock'

        out_relpath = root_relpath + '.js'
        out_file = basename(out_relpath)
        if production_mode:
            hashed_out_relpath = root_relpath
            hashed_out_relpath += '-' + build_hash + '.js'
        else:
            hashed_out_relpath = out_relpath
        hashed_out_file = basename(hashed_out_relpath)

        out_dir = dirname(self.relpath)
        self.url = urljoin(static_url, out_dir)
        self.component_relpath = relpath(path, ENTRIES_DIR)

        self.server = self.Env(
            entry=join(ENTRIES_DIR, 'server.js'),
            out_file=out_file,
            out_dir=join(BUNDLES_DIR, out_dir),
            script_relpath=relpath(server_script, ENTRIES_DIR),
            socket=join(SOCKETS_DIR, 'client', socket_relpath),
            cache_dir=join(CACHE_DIR, 'server')
        )
        self.client = self.Env(
            entry=join(ENTRIES_DIR, 'client.js'),
            out_file=hashed_out_file,
            out_dir=join(dist_dir, out_dir),
            script_relpath=relpath(client_script, ENTRIES_DIR),
            socket=join(SOCKETS_DIR, 'server', socket_relpath),
            cache_dir=join(CACHE_DIR, 'client')
        )

        self.script = urljoin(static_url, hashed_out_relpath)

        stylesheet_relpath = splitext(out_relpath)[0] + '.css'
        hashed_stylesheet_relpath = splitext(hashed_out_relpath)[0] + '.css'

        if exists(join(BUNDLES_DIR, stylesheet_relpath)):
            self.stylesheet = urljoin(static_url, hashed_stylesheet_relpath)
        else:
            self.stylesheet = ''

    def render(self, context: dict = None, request: HttpRequest = None) -> str:
        template_path = join(self.server.out_dir, self.server.out_file)
        try:
            return self.render_server.render(
                template_path, self.script, self.stylesheet, context)
        except Exception as exception:
            raise TemplateSyntaxError(exception)
