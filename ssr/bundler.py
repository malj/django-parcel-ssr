import json
from os import makedirs, remove, setsid, environ
from os.path import splitext, exists, dirname
from urllib.parse import quote_plus, urlencode
from subprocess import Popen, PIPE
from threading import Thread
from time import sleep
from typing import Callable, Dict
from requests import codes
from requests_unixsocket import Session
from .utils import wait_for_signal, read_output
from .bundle import Bundle
from .settings import Settings


class Bundler:
    session = Session()

    def __init__(self, bundle: Bundle, settings: Settings) -> None:
        self.bundle = bundle
        self.settings = settings

    def bundle_all(self) -> None:
        server_thread = Thread(target=self.bundle_server)
        client_thread = Thread(target=self.bundle_client)
        server_thread.start()
        client_thread.start()
        server_thread.join()
        client_thread.join()

    def bundle_server(self) -> None:
        if self.settings.env['NODE_ENV'] == 'production':
            self._bundle_server()
        else:
            self._watch(self.bundle.server.socket, self._bundle_server)

    def bundle_client(self) -> None:
        if self.settings.env['NODE_ENV'] == 'production':
            self._bundle_client()
        else:
            self._watch(self.bundle.client.socket, self._bundle_client)

    def _bundle_server(self) -> None:
        self._bundle({
            'SOCKET': self.bundle.server.socket,
            'COMPONENT': self.bundle.component_relpath,
            'SCRIPT': self.bundle.server.script_relpath,
            'PARCEL_OPTIONS': json.dumps({
                'entry': self.bundle.server.entry,
                'config': {
                    'outDir': self.bundle.server.out_dir,
                    'outFile': self.bundle.server.out_file,
                    'cache': self.settings.cache,
                    'cacheDir': self.bundle.server.cache_dir,
                    'sourceMaps': False,
                }
            })
        })

    def _bundle_client(self) -> None:
        self._bundle({
            'SOCKET': self.bundle.client.socket,
            'COMPONENT': self.bundle.component_relpath,
            'SCRIPT': self.bundle.client.script_relpath,
            'PARCEL_OPTIONS': json.dumps({
                'entry': self.bundle.client.entry,
                'config': {
                    'outDir': self.bundle.client.out_dir,
                    'outFile': self.bundle.client.out_file,
                    'cache': self.settings.cache,
                    'cacheDir': self.bundle.client.cache_dir,
                    'publicUrl': self.bundle.url
                }
            })
        })

    def _watch(self, socket: str, watcher: Callable) -> None:
        makedirs(dirname(socket), exist_ok=True)
        if exists(socket):
            if self._reconnect(socket):
                return
            remove(socket)
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
                sleep(0.1)

    def _get_url(self, socket: str) -> str:
        return 'http+unix://' + quote_plus(socket) + '?' + urlencode({
            'pid': self.settings.env['DJANGO_PID']
        })

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
        process = Popen([
            'node', self.settings.bundler
        ], stdout=PIPE, stderr=PIPE, preexec_fn=setsid, env={
            **environ,
            **self.settings.env,
            **env
        })
        if self.settings.env['NODE_ENV'] == 'production':
            read_output(process)
        else:
            stdout_thread = Thread(target=wait_for_signal, daemon=True, args=[
                process.stdout, self.settings.env['SIGNAL']
            ])
            stderr_thread = Thread(target=wait_for_signal, daemon=True, args=[
                process.stderr, self.settings.env['SIGNAL']
            ])
            stdout_thread.start()
            stderr_thread.start()
            stdout_thread.join()
            stderr_thread.join()
