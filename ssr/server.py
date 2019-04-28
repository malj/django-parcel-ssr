import json
from json.encoder import JSONEncoder
from os import makedirs, remove, setsid, environ
from os.path import join, dirname, exists
from urllib.parse import quote_plus, urlencode
from threading import Thread
from subprocess import Popen, PIPE
from requests import codes
from requests_unixsocket import Session
from typing import Dict
from ssr.settings import SERVER, SOCKETS_DIR
from ssr.utils import wait_for_signal


class Server:
    session = Session()
    socket = join(SOCKETS_DIR, 'renderer.sock')

    def __init__(self, env: Dict[str, str],
                 json_encoder: JSONEncoder = None) -> None:
        self.env = env
        self.json_encoder = json_encoder

    def get_url(self, pathname: str = '', params: dict = {}) -> str:
        host = quote_plus(self.socket)
        querystring = urlencode(params)
        return 'http+unix://' + host + pathname + '?' + querystring

    @property
    def exists(self) -> bool:
        url = self.get_url('', {
            'pid': self.env['DJANGO_PID']
        })
        try:
            response = self.session.get(url)
            if response.status_code == codes.ok:
                return True
        except:
            pass
        return False

    def run(self) -> None:
        if self.exists:
            return

        makedirs(dirname(self.socket), exist_ok=True)
        if exists(self.socket):
            remove(self.socket)

        process = Popen([
            'node', SERVER
        ], stdout=PIPE, stderr=PIPE, preexec_fn=setsid, env={
            **environ,
            **self.env,
            'SOCKET': self.socket,
        })
        stdout_thread = Thread(target=wait_for_signal, args=[
            process.stdout, self.env['SIGNAL']
        ])
        stderr_thread = Thread(target=wait_for_signal, args=[
            process.stderr, self.env['SIGNAL']
        ])
        stdout_thread.start()
        stderr_thread.start()
        stdout_thread.join()
        stderr_thread.join()

    def render(self, bundle: str, script: str, stylesheet: str,
               props: dict = None) -> str:
        url = self.get_url('/render', {
            'bundle': bundle,
            'props': json.dumps(props, cls=self.json_encoder),
            'script': script,
            'stylesheet': stylesheet,
        })
        response = self.session.get(url)
        if response.status_code == codes.ok:
            return response.text
        else:
            raise EnvironmentError(response.text)
