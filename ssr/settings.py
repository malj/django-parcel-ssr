from os import getpid, makedirs
from os.path import join, exists, dirname, abspath
from shutil import copytree, rmtree
from urllib.parse import urljoin
from platform import system
from tempfile import gettempdir
from uuid import uuid1
from django.conf import settings
from django.utils.module_loading import import_string
from django.core.serializers.json import DjangoJSONEncoder


class Settings:
    base_dir = join(settings.BASE_DIR, '.ssr')
    temp_dir = '/tmp' if system() == 'Darwin' else gettempdir()
    scripts_dir = join(base_dir, 'scripts')
    entries_dir = join(scripts_dir, 'entries')
    cache_dir = join(base_dir, 'cache')
    bundles_dir = join(base_dir, 'bundles')
    static_dir = join(base_dir, 'static')
    sockets_dir = join(temp_dir, 'ssr')
    socket = join(sockets_dir, 'renderer.sock')
    hash_file = join(base_dir, 'hash.txt')
    server = join(scripts_dir, 'server.mjs')
    bundler = join(scripts_dir, 'bundler.mjs')

    def __init__(self, options: dict) -> None:
        makedirs(self.base_dir, exist_ok=True)

        if exists(self.hash_file):
            with open(self.hash_file, 'r') as build_hash:
                self.build_hash = build_hash.read()
        else:
            self.build_hash = str(uuid1())
            with open(self.hash_file, 'w') as build_hash:
                build_hash.write(self.build_hash)

        env = options.pop('env')
        self.env = {
            **env,
            'WORKER_TTL': str(env['WORKER_TTL']),
            'SIGNAL': self.build_hash,
            'DJANGO_PID': str(getpid())
        }

        if 'output_dirname' in options:
            output_dirname = options.pop('output_dirname')
        else:
            output_dirname = 'dist/'

        self.static_url = urljoin(settings.STATIC_URL, output_dirname)
        self.dist_dir = join(self.static_dir, output_dirname)

        if exists(self.scripts_dir):
            rmtree(self.scripts_dir, ignore_errors=True)
        scripts_dir = join(dirname(abspath(__file__)), 'scripts')
        copytree(scripts_dir, self.scripts_dir)

        if 'json_encoder' in options:
            self.json_encoder = import_string(options.pop('json_encoder'))
        else:
            self.json_encoder = DjangoJSONEncoder

        if 'cache' in options:
            self.cache = options.pop('cache')
        else:
            self.cache = True

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
