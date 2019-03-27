import json
from os import makedirs, remove, setsid, environ
from os.path import join, dirname, exists
from urllib.parse import quote_plus, urlencode
from threading import Thread
from subprocess import Popen, PIPE
from requests import codes
from requests_unixsocket import Session
from .settings import Settings
from .utils import wait_for_signal
from .bundle import Bundle


class Server:
    socket_name = 'renderer.sock'
    session = Session()

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.socket = join(self.settings.sockets_dir, self.socket_name)

    def get_url(self, path: str = '', params: dict = {}) -> str:
        host = quote_plus(self.socket) + path
        querystring = urlencode(params)
        return 'http+unix://' + host + '?' + querystring

    @property
    def exists(self) -> bool:
        url = self.get_url('', {
            'pid': self.settings.env['DJANGO_PID']
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
            'node', self.settings.server
        ], stdout=PIPE, stderr=PIPE, preexec_fn=setsid, env={
            **environ,
            **self.settings.env,
            'SOCKET': self.socket,
        })
        stdout_thread = Thread(target=wait_for_signal, args=[
            process.stdout, self.settings.env['SIGNAL']
        ])
        stderr_thread = Thread(target=wait_for_signal, args=[
            process.stderr, self.settings.env['SIGNAL']
        ])
        stdout_thread.start()
        stderr_thread.start()
        stdout_thread.join()
        stderr_thread.join()

    def render(self, bundle: Bundle, props: dict = None) -> str:
        url = self.get_url('/render', {
            'bundle': join(bundle.server.out_dir, bundle.server.out_file),
            'props': json.dumps(props, cls=self.settings.json_encoder),
            'script': bundle.script,
            'stylesheet': bundle.stylesheet
        })
        response = self.session.get(url)
        if response.status_code == codes.ok:
            return response.text
        else:
            raise EnvironmentError(response.text)
