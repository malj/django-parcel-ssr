from django.template import TemplateSyntaxError
from django.http import HttpRequest
from .bundle import Bundle
from .server import Server


class Template:
    def __init__(self, bundle: Bundle, server: Server) -> None:
        self.bundle = bundle
        self.server = server

    def render(self, context: dict = None, request: HttpRequest = None) -> str:
        try:
            return self.server.render(self.bundle, context)
        except Exception as exception:
            raise TemplateSyntaxError(exception)
