from typing import Any, Awaitable, Optional
from . import BaseRequest


class AioHttpRequest(BaseRequest):
    def __init__(self, request):
        super().__init__(request)
        self._post = None

    async def post(self):
        if self._post is None:
            self._post = await self.request.post()

    async def get_argument(self,
                           name: str,
                           default: Any = None) -> Optional[str]:
        await self.post()
        return self._post.getone(name, default)

    async def get_arguments(self,
                            name: str) -> Optional[list]:
        await self.post()
        return self._post.getall(name, [])

    def get_query_argument(self,
                           name: str,
                           default: Any = None) -> Optional[str]:
        return self.request.query.getone(name, default)

    def get_query_arguments(self,
                            name: str) -> Optional[list]:
        return self.request.query.getall(name, [])

    def get_from_header(self,
                        name: str,
                        default: Any = None) -> Optional[dict]:
        return self.request.headers.get(name, default)

    def get_from_cookie(self,
                        name: str,
                        default: Any = None) -> Optional[str]:
        return self.request.cookies(name) or default

    def get_body(self) -> Awaitable[Optional[str]]:
        return self.request.text()

    def translate(self, message: str) -> str:
        return message

    def get_request_method(self) -> str:
        return self.request.method
