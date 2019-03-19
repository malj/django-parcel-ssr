name = 'ssr'


def setup():
    from .worker import Worker
    Worker().run()
