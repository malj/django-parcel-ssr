import os
import urllib.parse
import json
from json.encoder import JSONEncoder
from subprocess import Popen, PIPE
from threading import Thread
from requests import codes
from requests_unixsocket import Session
from typing import Dict, Any
from .utils import wait_for_signal

socket_name = 'renderer.sock'


def run(path: Dict[str, str], env: Dict[str, str]) -> None:
    socket = os.path.join(path['SOCKETS_DIR'], socket_name)
    host = urllib.parse.quote_plus(socket)
    querystring = urllib.parse.urlencode({
        'pid': env['DJANGO_PID']
    })
    url = 'http+unix://' + host + '?' + querystring

    try:
        response = Session().get(url)
        if response.status_code == codes.ok:
            return
    except:
        pass

    os.makedirs(os.path.dirname(socket), exist_ok=True)
    if os.path.exists(socket):
        os.remove(socket)

    argv = ['node', os.path.join(path['BASE_DIR'], 'scripts', 'server.mjs')]
    process = Popen(argv, stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid, env={
        **os.environ,
        **env,
        'SOCKET': socket,
    })

    stdout_thread = Thread(target=wait_for_signal, args=[
        process.stdout, env['SIGNAL']
    ])
    stderr_thread = Thread(target=wait_for_signal, args=[
        process.stderr, env['SIGNAL']
    ])

    stdout_thread.start()
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()


def render(bundle_name: str, script: str, stylesheet: str,
           path: Dict[str, str], props: Dict[str, Any] = None,
           encoder: JSONEncoder = None) -> str:
    socket = os.path.join(path['SOCKETS_DIR'], socket_name)
    host = urllib.parse.quote_plus(socket) + '/render'
    querystring = urllib.parse.urlencode({
        'bundle': os.path.join(path['BUNDLES_DIR'], bundle_name),
        'props': json.dumps(props, cls=encoder),
        'script': script,
        'stylesheet': stylesheet
    })
    url = 'http+unix://' + host + '?' + querystring
    response = Session().get(url)

    if response.status_code == codes.ok:
        return response.text
    else:
        raise EnvironmentError(response.text)
