from os.path import exists, join, dirname, abspath
from shutil import rmtree, copytree
from glob import glob
from threading import Thread
from django.template.backends.base import BaseEngine
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from typing import Dict
from .settings import Settings
from .server import Server
from .bundle import Bundle
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

        if 'extensions' in options:
            extensions = options.pop('extensions')
        else:
            extensions = ['js', 'jsx', 'ts', 'tsx']

        settings = Settings(options)
        server = Server(settings)
        server_thread = Thread(target=server.run)

        if exists(settings.scripts_dir):
            rmtree(settings.scripts_dir, ignore_errors=True)
        scripts_dir = join(dirname(abspath(__file__)), 'scripts')
        copytree(scripts_dir, settings.scripts_dir)

        threads = [server_thread]
        for template_dir in self.template_dirs:
            for extension in extensions:
                pattern = join(template_dir, '**', '*.' + extension)
                templates = glob(pattern, recursive=True)
                for template in templates:
                    bundle = Bundle(template, template_dir, settings)
                    bundler = Bundler(bundle, settings)

                    template = Template(bundle, server)
                    self.templates[bundle.relpath] = template

                    thread = Thread(target=bundler.bundle_all)
                    threads.append(thread)
        Worker(threads)

    def get_template(self, template_name: str) -> Template:
        if template_name in self.templates:
            return self.templates[template_name]
        else:
            raise TemplateDoesNotExist('Component not found', backend=self)
