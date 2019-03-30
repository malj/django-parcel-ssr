name = 'ssr'


def setup():
    from .worker import Worker
    worker = Worker()
    worker.use_server()
    if not worker.production_mode:
        worker.use_watchers()
    worker.run()
