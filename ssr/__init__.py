name = 'ssr'


def setup():
    from .worker import Worker
    worker = Worker()
    worker.run()
