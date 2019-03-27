from typing import List
from threading import Thread


class Worker():
    _state = {}  # type: dict

    def __init__(self, threads: List[Thread] = None) -> None:
        self.__dict__ = self._state
        if threads is not None:
            self._threads = threads

    @property
    def threads(self) -> List[Thread]:
        if hasattr(self, '_threads'):
            return self._threads
        else:
            raise EnvironmentError(
                'Server side rendering improperly configured. Did you forget '
                'to include the template engine in your Django settings?'
            )

    def run(self) -> None:
        for thread in self.threads:
            thread.start()
        for thread in self.threads:
            thread.join()
