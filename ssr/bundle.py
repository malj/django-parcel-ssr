from os.path import relpath, splitext, basename, join, dirname, exists
from urllib.parse import urljoin
from collections import namedtuple
from .settings import Settings


class Bundle:
    def __init__(self, path: str, root: str, settings: Settings) -> None:
        self.relpath = relpath(path, root)

        root_relpath = splitext(self.relpath)[0]
        socket_relpath = root_relpath + '-bundler.sock'

        out_relpath = root_relpath + '.js'
        out_file = basename(out_relpath)
        if settings.env['NODE_ENV'] == 'production':
            hashed_out_relpath = root_relpath
            hashed_out_relpath += '-' + settings.build_hash + '.js'
        else:
            hashed_out_relpath = out_relpath
        hashed_out_file = basename(hashed_out_relpath)

        out_dir = dirname(self.relpath)
        self.url = urljoin(settings.static_url, out_dir)
        self.component_relpath = relpath(path, settings.entries_dir)

        self.server = Env(
            entry=join(settings.entries_dir, 'server.js'),
            out_file=out_file,
            out_dir=join(settings.bundles_dir, out_dir),
            script_relpath=relpath(
                settings.server_script, settings.entries_dir),
            socket=join(settings.sockets_dir, 'client', socket_relpath),
            cache_dir=join(settings.cache_dir, 'server')
        )
        self.client = Env(
            entry=join(settings.entries_dir, 'client.js'),
            out_file=hashed_out_file,
            out_dir=join(settings.dist_dir, out_dir),
            script_relpath=relpath(
                settings.client_script, settings.entries_dir),
            socket=join(settings.sockets_dir, 'server', socket_relpath),
            cache_dir=join(settings.cache_dir, 'client')
        )

        self.script = urljoin(settings.static_url, hashed_out_relpath)
        stylesheet_relpath = splitext(hashed_out_relpath)[0] + '.css'
        if exists(join(settings.bundles_dir, stylesheet_relpath)):
            self.stylesheet = urljoin(settings.static_url, stylesheet_relpath)
        else:
            self.stylesheet = ''


Env = namedtuple('Env', [
    'entry',
    'out_file',
    'out_dir',
    'script_relpath',
    'socket',
    'cache_dir'
])
