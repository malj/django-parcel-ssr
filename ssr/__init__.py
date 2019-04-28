name = 'ssr'


def setup():
    from ssr import worker
    worker.use_server()
    if not worker.production_mode:
        worker.use_watchers()
    worker.run()
