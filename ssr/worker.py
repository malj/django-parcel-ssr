from typing import List
from threading import Thread


class Worker():
    _state = {}  # type: ignore

    def __init__(self, threads: List[Thread] = None) -> None:
        self.__dict__ = self._state
        if threads is not None:
            self.threads = threads

    def run(self) -> None:
        if not hasattr(self, 'threads'):
            raise EnvironmentError(
                'Server side rendering improperly configured. Did you forget '
                'to include the template engine in your Django settings?')

        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()
