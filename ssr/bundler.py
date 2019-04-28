import json
from os import makedirs, remove, setsid, environ
from os.path import exists, dirname
from urllib.parse import quote_plus, urlencode
from subprocess import Popen, PIPE
from threading import Thread
from time import sleep
from typing import Callable, Dict
from requests import codes
from requests_unixsocket import Session
from ssr.settings import BUNDLER
from ssr.template import Template
from ssr.utils import wait_for_signal, read_output


class Bundler:
    session = Session()

    def __init__(self, template: Template,
                 env: Dict[str, str], cache: bool) -> None:
        self.template = template
        self.env = env
        self.cache = cache

    def get_server_env(self, watch: bool) -> Dict[str, str]:
        return {
            'SOCKET': self.template.server.socket,
            'COMPONENT': self.template.component_relpath,
            'SCRIPT': self.template.server.script_relpath,
            'PARCEL_OPTIONS': json.dumps({
                'entry': self.template.server.entry,
                'config': {
                    'outDir': self.template.server.out_dir,
                    'outFile': self.template.server.out_file,
                    'cache': self.cache,
                    'cacheDir': self.template.server.cache_dir,
                    'watch': watch,
                    'sourceMaps': False
                }
            })
        }

    def get_client_env(self, watch: bool) -> Dict[str, str]:
        return {
            'SOCKET': self.template.client.socket,
            'COMPONENT': self.template.component_relpath,
            'SCRIPT': self.template.client.script_relpath,
            'PARCEL_OPTIONS': json.dumps({
                'entry': self.template.client.entry,
                'config': {
                    'outDir': self.template.client.out_dir,
                    'outFile': self.template.client.out_file,
                    'cache': self.cache,
                    'cacheDir': self.template.client.cache_dir,
                    'watch': watch,
                    'publicUrl': self.template.url
                }
            })
        }

    def build(self) -> None:
        server_env = self.get_server_env(False)
        client_env = self.get_client_env(False)
        server_thread = Thread(target=self.bundle, args=[server_env, False])
        client_thread = Thread(target=self.bundle, args=[client_env, False])
        self.run(server_thread, client_thread)

    def watch(self) -> None:
        server_env = self.get_server_env(True)
        client_env = self.get_client_env(True)
        server_thread = Thread(target=self.prepare, args=[
            self.template.server.socket, lambda: self.bundle(server_env, True)
        ])
        client_thread = Thread(target=self.prepare, args=[
            self.template.client.socket, lambda: self.bundle(client_env, True)
        ])
        self.run(server_thread, client_thread)

    def run(self, server_thread: Thread, client_thread: Thread) -> None:
        server_thread.start()
        client_thread.start()
        server_thread.join()
        client_thread.join()

    def prepare(self, socket: str, watcher: Callable[[], None]) -> None:
        makedirs(dirname(socket), exist_ok=True)
        if exists(socket):
            if self.reconnect(socket):
                return
            remove(socket)
        watcher()
        self.connect(socket)

    def poll(self, socket: str) -> None:
        url = self.get_url(socket)
        while True:
            response = self.session.get(url)
            message = response.content.strip(b' ')
            if message:
                print(message.decode('utf-8')[:-1])
            else:
                sleep(0.1)

    def get_url(self, socket: str) -> str:
        return 'http+unix://' + quote_plus(socket) + '?' + urlencode({
            'pid': self.env['DJANGO_PID']
        })

    def connect(self, socket: str) -> None:
        Thread(target=self.poll, daemon=True, args=[socket]).start()

    def reconnect(self, socket: str) -> bool:
        try:
            url = self.get_url(socket)
            response = self.session.get(url)
            connection_exists = response.status_code == codes.ok
            if connection_exists:
                self.connect(socket)
            return connection_exists
        except:
            return False

    def bundle(self, env: Dict[str, str], watch: bool) -> None:
        process = Popen([
            'node', BUNDLER
        ], stdout=PIPE, stderr=PIPE, preexec_fn=setsid, env={
            **environ,
            **self.env,
            **env
        })
        if watch:
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
        else:
            read_output(process)
