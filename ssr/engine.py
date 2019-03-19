import os
from django.utils.module_loading import import_string
from django.core.serializers.json import DjangoJSONEncoder
from typing import Dict, Any
from .server import render
from .bundler import Bundler


class Engine:
    def __init__(self, bundle_hash: str, static_url: str, path: Dict[str, str],
                 env: Dict[str, str], json_encoder: str = None) -> None:
        self.bundle_hash = bundle_hash
        self.static_url = static_url
        self.path = path
        self.env = env
        if json_encoder:
            self.json_encoder = import_string(json_encoder)
        else:
            self.json_encoder = DjangoJSONEncoder

    def render(self, component: str, props: Dict[str, Any] = None) -> str:
        bundle_name = Bundler.get_bundle_name(component)
        bundle = os.path.join(self.path['BUNDLES_DIR'], bundle_name)
        script = Bundler.get_script(
            component, self.bundle_hash, self.static_url, self.env['NODE_ENV']
        )
        stylesheet = Bundler.get_stylesheet(
            component, self.bundle_hash, self.path['BUNDLES_DIR'],
            self.static_url, self.env['NODE_ENV']
        )
        return render(
            bundle, script, stylesheet, self.path, props, self.json_encoder
        )
