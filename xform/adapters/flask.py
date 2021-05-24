from typing import Any, Optional
from . import BaseRequest


class FlaskRequest(BaseRequest):
    def __init__(self, request):
        super().__init__(request)

    def get_argument(self,
                     name: str,
                     default: Any = None) -> Optional[str]:
        return self.request.form.get(name, default=default)

    def get_arguments(self,
                      name: str) -> Optional[list]:
        return self.request.form.getlist(name, [])

    def get_query_argument(self,
                           name: str,
                           default: Any = None) -> Optional[str]:
        return self.request.args.get(name, default=default)

    def get_query_arguments(self,
                            name: str) -> Optional[list]:
        return self.request.args.getlist(name, [])

    def get_from_header(self,
                        name: str,
                        default: Any = None) -> Optional[dict]:
        return self.request.headers.get(name, default)

    def get_from_cookie(self,
                        name: str,
                        default: Any = None) -> Optional[str]:
        return self.request.cookies.get(name, default)

    def get_body(self) -> Optional[str]:
        # If there are other components calling before calling,
        # please set get_data(cache=True) otherwise no data can be obtained
        return self.request.get_data(cache=True, as_text=True)

    def translate(self, message: str) -> str:
        return message

    def get_request_method(self) -> str:
        return self.request.method
