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
from typing import Dict, List
from ssr.settings import HASH_FILE, SCRIPTS_DIR, BASE_DIR, STATIC_DIR
from ssr.server import Server
from ssr.bundler import Bundler
from ssr.template import Template


class Components(BaseEngine):
    app_dirname = 'bundles'
    templates = {}  # type: Dict[str, Template]

    def __init__(self, params: dict) -> None:
        params = params.copy()
        self.options = params.pop('OPTIONS').copy()
        super().__init__(params)

    def setup(self) -> None:
        makedirs(BASE_DIR, exist_ok=True)

        if exists(SCRIPTS_DIR):
            rmtree(SCRIPTS_DIR, ignore_errors=True)
        scripts_dir = join(dirname(dirname(abspath(__file__))), 'scripts')
        copytree(scripts_dir, SCRIPTS_DIR)

        if exists(HASH_FILE):
            with open(HASH_FILE, 'r') as hash_file:
                build_hash = hash_file.read()
        else:
            build_hash = str(uuid1())
            with open(HASH_FILE, 'w') as hash_file:
                hash_file.write(build_hash)

        env = {
            'NODE_ENV': 'development' if settings.DEBUG else 'production',
            'NODE_OPTIONS': '--experimental-modules --no-warnings',
            'WORKER_TTL': '1000'
        }  # Dict[str, str]

        if 'env' in self.options:
            env.update(self.options['env'])

        env.update({
            'WORKER_TTL': str(env['WORKER_TTL']),
            'SIGNAL': build_hash,
            'DJANGO_PID': str(getpid())
        })

        self.production_mode = env['NODE_ENV'] == 'production'

        if 'json_encoder' in self.options:
            json_encoder = import_string(self.options['json_encoder'])
        else:
            json_encoder = DjangoJSONEncoder

        self.server = Server(env, json_encoder)

        if 'output_dirname' in self.options:
            output_dirname = self.options['output_dirname']
        else:
            output_dirname = 'dist/'

        static_url = urljoin(settings.STATIC_URL, output_dirname)
        dist_dir = join(STATIC_DIR, output_dirname)

        scripts = {
            'server': join(SCRIPTS_DIR, 'react', 'server.js'),
            'client': join(SCRIPTS_DIR, 'react', 'client.js'),
        }
        if 'scripts' in self.options:
            scripts.update(self.options['scripts'])

        if 'extensions' in self.options:
            extensions = self.options['extensions']
        else:
            extensions = ['js', 'jsx', 'ts', 'tsx']

        if 'cache' in self.options:
            cache = self.options['cache']
        else:
            cache = True

        self.bundlers = []  # type: List[Bundler]

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
                        server=self.server,
                        build_hash=build_hash
                    )
                    self.templates[template.relpath] = template
                    bundler = Bundler(template, env, cache)
                    self.bundlers.append(bundler)

    def get_template(self, template_name: str) -> Template:
        if template_name in self.templates:
            return self.templates[template_name]
        else:
            raise TemplateDoesNotExist('Component not found', backend=self)
