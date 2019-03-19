import os
import json
import time
import urllib.parse
from subprocess import Popen, PIPE
from threading import Thread
from typing import Dict, Callable
from requests import codes
from requests_unixsocket import Session
from .utils import wait_for_signal, read_output


class Bundler:
    session = Session()

    def __init__(self, component: str, bundle_hash: str, static_url: str,
                 path: Dict[str, str],  env: Dict[str, str],
                 cache: bool, scripts: Dict[str, str]) -> None:
        self.component = component
        self.hash = bundle_hash
        self.static_url = static_url
        self.path = path
        self.env = env
        self.cache = cache
        self.scripts = scripts
        self.argv = [
            'node', os.path.join(self.path['SCRIPTS_DIR'], 'bundler.mjs')
        ]
        self.server_entry = os.path.join(
            self.path['SCRIPTS_DIR'],  'entries', 'server.js'
        )
        self.client_entry = os.path.join(
            self.path['SCRIPTS_DIR'], 'entries', 'client.js'
        )
        socket_name = os.path.splitext(
            self.component_name)[0] + '-bundler.sock'
        self.client_socket = os.path.join(
            self.path['SOCKETS_DIR'], 'client', socket_name
        )
        self.server_socket = os.path.join(
            self.path['SOCKETS_DIR'], 'server', socket_name
        )

    @property
    def component_name(self) -> str:
        return Bundler.get_component_name(self.component)

    @property
    def bundle_name(self) -> str:
        return Bundler.get_bundle_name(self.component)

    @property
    def hashed_bundle_name(self) -> str:
        return Bundler.get_hashed_bundle_name(
            self.component, self.hash, self.env['NODE_ENV'])

    @staticmethod
    def get_component_name(component: str) -> str:
        return os.path.basename(component)

    @staticmethod
    def get_bundle_name(component: str) -> str:
        name = os.path.splitext(Bundler.get_component_name(component))[0]
        return name + '.js'

    @staticmethod
    def get_hashed_bundle_name(component: str, bundle_hash: str,
                               node_env: str) -> str:
        bundle_name = Bundler.get_bundle_name(component)
        if node_env == 'production':
            name = os.path.splitext(bundle_name)[0]
            return name + '-' + bundle_hash + '.js'
        else:
            return bundle_name

    @staticmethod
    def get_script(component: str, bundle_hash: str, static_url: str,
                   node_env: str) -> str:
        name = Bundler.get_hashed_bundle_name(component, bundle_hash, node_env)
        return urllib.parse.urljoin(static_url, name)

    @staticmethod
    def get_stylesheet(component: str, bundle_hash: str, bundle_dir: str,
                       static_url: str, node_env: str) -> str:
        name = Bundler.get_bundle_name(component)
        name = os.path.splitext(name)[0] + '.css'
        hashed_name = Bundler.get_hashed_bundle_name(
            component, bundle_hash, node_env
        )
        hashed_name = os.path.splitext(hashed_name)[0] + '.css'

        if os.path.exists(os.path.join(bundle_dir, name)):
            return urllib.parse.urljoin(static_url, hashed_name)
        else:
            return ''

    def bundle(self) -> None:
        client_thread = Thread(target=self.bundle_client)
        server_thread = Thread(target=self.bundle_server)

        server_thread.start()
        client_thread.start()

        server_thread.join()
        client_thread.join()

    def bundle_server(self) -> None:
        if self.env['NODE_ENV'] == 'production':
            self._bundle_server()
        else:
            self._watch(self.server_socket, self._bundle_server)

    def bundle_client(self) -> None:
        if self.env['NODE_ENV'] == 'production':
            self._bundle_client()
        else:
            self._watch(self.client_socket, self._bundle_client)

    def _bundle_server(self) -> None:
        entry_dir = os.path.dirname(self.server_entry)
        component = os.path.relpath(self.component, entry_dir)
        create_renderer = os.path.relpath(self.scripts['server'], entry_dir)

        self._bundle({
            'SOCKET': self.server_socket,
            'SSR_COMPONENT': component,
            'SSR_CREATE_RENDERER': create_renderer,
            'PARCEL_OPTIONS': json.dumps({
                'entry': self.server_entry,
                'config': {
                    'outDir': self.path['BUNDLES_DIR'],
                    'outFile': self.bundle_name,
                    'cache': self.cache,
                    'cacheDir': os.path.join(self.path['CACHE_DIR'], 'server')
                }
            })
        })

    def _bundle_client(self) -> None:
        entry_dir = os.path.dirname(self.client_entry)
        component = os.path.relpath(self.component, entry_dir)
        hydrate = os.path.relpath(self.scripts['client'], entry_dir)

        self._bundle({
            'SOCKET': self.client_socket,
            'SSR_COMPONENT': component,
            'SSR_HYDRATE': hydrate,
            'PARCEL_OPTIONS': json.dumps({
                'entry': self.client_entry,
                'config': {
                    'outDir': self.path['DIST_DIR'],
                    'outFile': self.hashed_bundle_name,
                    'publicUrl': self.static_url,
                    'cache': self.cache,
                    'cacheDir': os.path.join(self.path['CACHE_DIR'], 'client')
                }
            })
        })

    def _watch(self, socket: str, watcher: Callable) -> None:
        os.makedirs(os.path.dirname(socket), exist_ok=True)
        if os.path.exists(socket):
            if self._reconnect(socket):
                return
            os.remove(socket)
        watcher()
        self._connect(socket)

    def _poll(self, socket: str) -> None:
        url = self._get_url(socket)
        while True:
            response = self.session.get(url)
            message = response.content.strip(b' ')
            if message:
                print(message.decode('utf-8')[:-1])
            else:
                time.sleep(0.1)

    def _get_url(self, socket: str) -> str:
        host = urllib.parse.quote_plus(socket)
        querystring = urllib.parse.urlencode({
            'pid': self.env['DJANGO_PID']
        })
        return 'http+unix://' + host + '?' + querystring

    def _connect(self, socket: str) -> None:
        Thread(target=self._poll, daemon=True, args=[socket]).start()

    def _reconnect(self, socket: str) -> bool:
        try:
            url = self._get_url(socket)
            response = self.session.get(url)
            connection_exists = response.status_code == codes.ok
            if connection_exists:
                self._connect(socket)
            return connection_exists
        except:
            return False

    def _bundle(self, env: Dict[str, str] = {}) -> None:
        process = Popen(
            self.argv, stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid, env={
                **os.environ,
                **self.env,
                **env
            }
        )
        if self.env['NODE_ENV'] == 'production':
            read_output(process)
        else:
            stdout_thread = Thread(target=wait_for_signal, daemon=True, args=[
                process.stdout, self.env['SIGNAL']
            ])
            stderr_thread = Thread(target=wait_for_signal, daemon=True, args=[
                process.stderr, self.env['SIGNAL']
            ])

            stdout_thread.start()
            stderr_thread.start()

            stdout_thread.join()
            stderr_thread.join()
