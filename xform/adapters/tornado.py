from typing import Any, Optional
from . import BaseRequest


class TornadoRequest(BaseRequest):
    def __init__(self, request):
        super().__init__(request)

    def get_argument(self,
                     name: str,
                     default: Any = None) -> Optional[str]:
        return self.request.get_argument(name, default=default)

    def get_arguments(self,
                      name: str) -> Optional[list]:
        return self.request.get_arguments(name)

    def get_query_argument(self,
                           name: str,
                           default: Any = None) -> Optional[str]:
        return self.request.get_query_argument(name, default=default)

    def get_query_arguments(self,
                            name: str) -> Optional[list]:
        return self.request.get_query_arguments(name)

    def get_from_header(self,
                        name: str,
                        default: Any = None) -> Optional[dict]:
        return self.request.request.headers.get(name, default)

    def get_from_cookie(self,
                        name: str,
                        default: Any = None) -> Optional[str]:
        return self.request.get_cookie(name, default=default)

    def get_body(self) -> Optional[str]:
        return self.request.request.body

    def translate(self, message: str) -> str:
        return self.request.locale.translate(message)

    def get_request_method(self) -> str:
        return self.request.request.method
