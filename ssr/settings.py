from os import getpid
from os.path import join
from urllib.parse import urljoin
from platform import system
from tempfile import gettempdir
from uuid import uuid1
from django.conf import settings
from django.utils.module_loading import import_string
from django.core.serializers.json import DjangoJSONEncoder


class Settings:
    build_hash = str(uuid1())
    base_dir = join(settings.BASE_DIR, '.ssr')
    temp_dir = '/tmp' if system() == 'Darwin' else gettempdir()
    scripts_dir = join(base_dir, 'scripts')
    entries_dir = join(scripts_dir, 'entries')
    cache_dir = join(base_dir, 'cache')
    bundles_dir = join(base_dir, 'bundles')
    sockets_dir = join(temp_dir, 'ssr')
    socket = join(sockets_dir, 'renderer.sock')
    server = join(scripts_dir, 'server.mjs')
    bundler = join(scripts_dir, 'bundler.mjs')

    def __init__(self, options: dict) -> None:
        env = {
            'NODE_ENV': 'development' if settings.DEBUG else 'production',
            'NODE_OPTIONS': '--experimental-modules --no-warnings',
            'WORKER_TTL': 1000
        }
        if 'env' in options:
            env = {
                **env,
                **options.pop('env')
            }
        self.env = {
            **env,  # type: ignore
            'WORKER_TTL': str(env['WORKER_TTL']),
            'SIGNAL': self.build_hash,
            'DJANGO_PID': str(getpid())
        }

        if 'json_encoder' in options:
            self.json_encoder = import_string(options.pop('json_encoder'))
        else:
            self.json_encoder = DjangoJSONEncoder

        if 'cache' in options:
            self.cache = options.pop('cache')
        else:
            self.cache = True

        if 'output_dirname' in options:
            output_dirname = options.pop('output_dirname')
        else:
            output_dirname = 'dist/'

        self.static_url = urljoin(settings.STATIC_URL, output_dirname)
        self.dist_dir = join(self.base_dir, 'static', output_dirname)

        scripts = {
            'server': join(self.scripts_dir, 'react', 'server.js'),
            'client': join(self.scripts_dir, 'react', 'client.js'),
        }
        if 'scripts' in options:
            scripts = {
                **scripts,
                **options.pop('scripts')
            }
        self.server_script = scripts['server']
        self.client_script = scripts['client']
