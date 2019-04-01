from os import getpid, makedirs
from os.path import join, dirname, abspath, exists
from shutil import rmtree, copytree
from urllib.parse import urljoin
from glob import glob
from uuid import uuid1
from django.template.backends.base import BaseEngine
from django.template import TemplateDoesNotExist
from django.utils.module_loading import import_string
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from typing import Dict, List, Tuple
from .settings import HASH_FILE, SCRIPTS_DIR, BASE_DIR, STATIC_DIR
from .server import Server
from .bundler import Bundler
from .worker import Worker
from .template import Template


class Components(BaseEngine):
    app_dirname = 'bundles'
    templates = {}  # type: Dict[str, Template]

    def __init__(self, params: dict) -> None:
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        super().__init__(params)

        env = {
            'NODE_ENV': 'development' if settings.DEBUG else 'production',
            'NODE_OPTIONS': '--experimental-modules --no-warnings',
            'WORKER_TTL': 1000
        }
        if 'env' in options:
            env = {
                **env,
                **options['env']
            }
        options['env'] = env
        Worker(env['NODE_ENV'] == 'production', lambda: self.setup(options))

    def setup(self, options: dict) -> Tuple[Server, List[Bundler]]:
        makedirs(BASE_DIR, exist_ok=True)

        if exists(SCRIPTS_DIR):
            rmtree(SCRIPTS_DIR, ignore_errors=True)
        copytree(join(dirname(abspath(__file__)), 'scripts'), SCRIPTS_DIR)

        if exists(HASH_FILE):
            with open(HASH_FILE, 'r') as hash_file:
                build_hash = hash_file.read()
        else:
            build_hash = str(uuid1())
            with open(HASH_FILE, 'w') as hash_file:
                hash_file.write(build_hash)

        env = {
            **options['env'],
            'WORKER_TTL': str(options['env']['WORKER_TTL']),
            'SIGNAL': build_hash,
            'DJANGO_PID': str(getpid())
        }

        if 'json_encoder' in options:
            json_encoder = import_string(options['json_encoder'])
        else:
            json_encoder = DjangoJSONEncoder

        server = Server(env, json_encoder)

        if 'output_dirname' in options:
            output_dirname = options['output_dirname']
        else:
            output_dirname = 'dist/'

        static_url = urljoin(settings.STATIC_URL, output_dirname)
        dist_dir = join(STATIC_DIR, output_dirname)

        scripts = {
            'server': join(SCRIPTS_DIR, 'react', 'server.js'),
            'client': join(SCRIPTS_DIR, 'react', 'client.js'),
        }
        if 'scripts' in options:
            scripts = {
                **scripts,
                **options['scripts']
            }

        if 'extensions' in options:
            extensions = options['extensions']
        else:
            extensions = ['js', 'jsx', 'ts', 'tsx']

        if 'cache' in options:
            cache = options['cache']
        else:
            cache = True

        bundlers = []

        for template_dir in self.template_dirs:
            for extension in extensions:
                pattern = join(template_dir, '**', '*.' + extension)
                paths = glob(pattern, recursive=True)
                for path in paths:
                    template = Template(
                        path=path,
                        root=template_dir,
                        production_mode=env['NODE_ENV'] == 'production',
                        static_url=static_url,
                        server_script=scripts['server'],
                        client_script=scripts['client'],
                        dist_dir=dist_dir,
                        server=server,
                        build_hash=build_hash
                    )
                    self.templates[template.relpath] = template
                    bundler = Bundler(template, env, cache)
                    bundlers.append(bundler)

        return server, bundlers

    def get_template(self, template_name: str) -> Template:
        if template_name in self.templates:
            return self.templates[template_name]
        else:
            raise TemplateDoesNotExist('Component not found', backend=self)
