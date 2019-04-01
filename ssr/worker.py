from typing import List, Tuple, Callable
from threading import Thread
from .server import Server
from .bundler import Bundler


class Worker:
    state = {}  # type: dict

    def __init__(
        self,
        production_mode: bool = None,
        setup: Callable[[], Tuple[Server, List[Bundler]]] = None
    ) -> None:
        self.__dict__ = self.state
        if production_mode is not None:
            self.production_mode = production_mode
        if setup is not None:
            self.setup = setup
            self.threads = []  # type: List[Thread]

    def __getattr__(self, name: str):
        if name in ('server', 'bundlers'):
            self.server, self.bundlers = self.setup()
            return getattr(self, name)

        if name in ('production_mode', 'setup', 'threads'):
            raise EnvironmentError(
                'Server side rendering improperly configured. Did you forget '
                'to include the template engine in your Django settings?'
            )

    def use_server(self) -> None:
        self.threads.append(Thread(target=self.server.run))

    def use_builders(self) -> None:
        for bundler in self.bundlers:
            self.threads.append(Thread(target=bundler.build))

    def use_watchers(self) -> None:
        for bundler in self.bundlers:
            self.threads.append(Thread(target=bundler.watch))

    def run(self) -> None:
        for thread in self.threads:
            thread.start()
        for thread in self.threads:
            thread.join()
