from os.path import join
from glob import glob
from django.template.backends.base import BaseEngine
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.conf import settings
from typing import Dict, List, Tuple
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
        env = {
            'NODE_ENV': 'development' if settings.DEBUG else 'production',
            'NODE_OPTIONS': '--experimental-modules --no-warnings',
            'WORKER_TTL': 1000
        }
        options['env'] = env if 'env' not in options else {
            **env,
            **options['env']
        }
        Worker(
            production_mode=options['env']['NODE_ENV'] == 'production',
            setup=lambda: self.setup(options)
        )

    def setup(self, options: dict) -> Tuple[Server, List[Bundler]]:
        if 'extensions' in options:
            extensions = options.pop('extensions')
        else:
            extensions = ['js', 'jsx', 'ts', 'tsx']

        settings = Settings(options)
        server = Server(settings)
        bundlers = []

        for template_dir in self.template_dirs:
            for extension in extensions:
                pattern = join(template_dir, '**', '*.' + extension)
                templates = glob(pattern, recursive=True)
                for template in templates:
                    bundle = Bundle(template, template_dir, settings)
                    bundlers.append(Bundler(bundle, settings))
                    self.templates[bundle.relpath] = Template(bundle, server)

        return server, bundlers

    def get_template(self, template_name: str) -> Template:
        if template_name in self.templates:
            return self.templates[template_name]
        else:
            raise TemplateDoesNotExist('Component not found', backend=self)
