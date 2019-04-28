from django.template import engines
from django.template.utils import InvalidTemplateEngineError
from threading import Thread
from typing import List
from ssr.backends import javascript

threads = []  # type: List[Thread]

try:
    engine = engines['javascript']  # type: javascript.Components
except InvalidTemplateEngineError:
    raise EnvironmentError(
        'Server side rendering improperly configured. Did you forget '
        'to include the template engine in your Django settings?'
    )

engine.setup()
production_mode = engine.production_mode


def use_server() -> None:
    threads.append(Thread(target=engine.server.run))


def use_builders() -> None:
    for bundler in engine.bundlers:
        threads.append(Thread(target=bundler.build))


def use_watchers() -> None:
    for bundler in engine.bundlers:
        threads.append(Thread(target=bundler.watch))


def run() -> None:
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
