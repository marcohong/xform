from typing import Any, Optional
from . import BaseRequest
from xform.utils import parse_content_type


class SanicRequest(BaseRequest):
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
        ctype = parse_content_type(self.get_from_header('Content-Type', ''))
        charset = ctype.parameters.get('charset') or 'utf-8'
        return self.request.body.decode(charset)

    def translate(self, message: str) -> str:
        return message

    def get_request_method(self) -> str:
        return self.request.method
