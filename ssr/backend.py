import os
import platform
import urllib.parse
from threading import Thread
from shutil import rmtree, copytree
from django.http import HttpRequest
from django.template.backends.base import BaseEngine
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.conf import settings
from uuid import uuid1
from glob import glob
from tempfile import gettempdir
from .engine import Engine
from .bundler import Bundler
from .server import run as run_server
from .worker import Worker


class Components(BaseEngine):
    app_dirname = 'bundles'

    def __init__(self, params: dict) -> None:
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        super().__init__(params)

        bundle_hash = str(uuid1())
        env = {
            'NODE_ENV': 'development' if settings.DEBUG else 'production',
            'NODE_OPTIONS': '--experimental-modules --no-warnings',
            'WORKER_TTL': 1000,
        }
        if 'env' in options:
            env = {
                **env,
                **options.pop('env')
            }
        env = {
            **env,
            'SIGNAL': bundle_hash,
            'DJANGO_PID': str(os.getpid()),
            'WORKER_TTL': str(env['WORKER_TTL']),
        }

        if 'extensions' in options:
            extensions = options.pop('extensions')
        else:
            extensions = ['js', 'jsx', 'ts', 'tsx']

        if 'output_dir' in options:
            output_dir = options.pop('output_dir')
        else:
            output_dir = 'dist/'

        if 'json_encoder' in options:
            json_encoder = options.pop('json_encoder')
        else:
            json_encoder = None

        if 'cache' in options:
            cache = options.pop('cache')
        else:
            cache = True

        STATIC_URL = urllib.parse.urljoin(settings.STATIC_URL, output_dir)
        BASE_DIR = os.path.join(settings.BASE_DIR, '.ssr')

        if platform.system() == 'Darwin':
            TEMP_DIR = '/tmp'
        else:
            TEMP_DIR = gettempdir()

        self.path = {
            'BASE_DIR': BASE_DIR,
            'SCRIPTS_DIR': os.path.join(BASE_DIR, 'scripts'),
            'DIST_DIR': os.path.join(BASE_DIR, 'static', output_dir),
            'CACHE_DIR': os.path.join(BASE_DIR, 'cache'),
            'BUNDLES_DIR': os.path.join(BASE_DIR, 'bundles'),
            'SOCKETS_DIR': os.path.join(TEMP_DIR, 'ssr'),
        }

        if os.path.exists(self.path['SCRIPTS_DIR']):
            rmtree(self.path['SCRIPTS_DIR'], ignore_errors=True)

        copytree(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'scripts'),
            self.path['SCRIPTS_DIR'])

        scripts = {
            'server': os.path.join(
                self.path['SCRIPTS_DIR'], 'react', 'server.js'),
            'client': os.path.join(
                self.path['SCRIPTS_DIR'], 'react', 'client.js'),
        }

        if 'scripts' in options:
            scripts = {
                **scripts,
                **options.pop('scripts')
            }

        self.engine = Engine(bundle_hash, STATIC_URL,  # type: ignore
                             self.path, env, json_encoder)

        if env['NODE_ENV'] == 'production':
            for build_dir in (self.path['BUNDLES_DIR'], self.path['DIST_DIR']):
                if os.path.exists(build_dir):
                    rmtree(build_dir, ignore_errors=True)

        server_thread = Thread(target=run_server,  args=[self.path, env])
        threads = [server_thread]
        for template_dir in self.template_dirs:
            for extension in extensions:
                pattern = os.path.join(template_dir, '*.' + extension)
                templates = glob(pattern, recursive=True)
                for template in templates:
                    bundler = Bundler(  # type: ignore
                        template, bundle_hash, STATIC_URL, self.path,
                        env, cache, scripts)
                    thread = Thread(target=bundler.bundle)
                    threads.append(thread)

        Worker(threads)

    def get_template(self, template_name: str) -> 'Template':
        template_name = os.path.splitext(template_name)[0] + '.js'
        template = os.path.join(self.path['BUNDLES_DIR'], template_name)

        if os.path.isfile(template):
            return Template(template, backend=self)
        else:
            raise TemplateDoesNotExist('Component not found', backend=self)


class Template:
    def __init__(self, template: str, backend: Components) -> None:
        self.template = template
        self.backend = backend

    def render(self, context: dict = None, request: HttpRequest = None) -> str:
        try:
            return self.backend.engine.render(self.template, context)
        except Exception as exception:
            raise TemplateSyntaxError(exception)
