import threading
from typing import Any, Optional

__all__ = ['BaseRequest', 'TornadoRequest', 'HttpRequest']


class BaseRequest:
    def __init__(self, request) -> None:
        self.request = request

    def get_argument(self,
                     name: str,
                     default: Any = None) -> Optional[str]:
        '''
        Get param from submit form.

        :param name: <str>
        :param default: <str>
        :return: <str>
        '''
        raise NotImplementedError

    def get_arguments(self,
                      name: str,
                      default: list = None) -> Optional[list]:
        '''
        Get params from submit form.

        :param name: <str>
        :param default: <str>
        :return: <list>
        '''
        raise NotImplementedError

    def get_query_argument(self,
                           name: str,
                           default: Any = None) -> Optional[str]:
        '''
        Get param from query string.

        :param name: <str>
        :param default: <str>
        :return: <str>
        '''
        raise NotImplementedError

    def get_query_arguments(self,
                            name: str,
                            default: list = None) -> Optional[list]:
        '''
        Get params from query string.

        :param name: <str>
        :param default: <str>
        :return: <list>
        '''
        raise NotImplementedError

    def get_from_header(self, name: str, default: Any = None) -> Optional[str]:
        '''
        Get param from headers.

        :param name: <str>
        :param default: <str>
        :return: <str>
        '''
        raise NotImplementedError

    def get_from_cookie(self, name: str, default: Any = None) -> Optional[str]:
        '''
        Get param from cookies.

        :param name: <str>
        :param default: <str>
        :return: <str>
        '''
        raise NotImplementedError

    def get_body(self) -> Optional[str]:
        '''
        Get request body.

        :return: <str>
        '''
        raise NotImplementedError

    def translate(self, message: str) -> str:
        '''
        Translation message

        :param message: <str>
        :return: <str>
        '''
        return message


class TornadoRequest(BaseRequest):
    def __init__(self, request):
        super().__init__(request)

    def get_argument(self,
                     name: str,
                     default: Any = None) -> Optional[str]:
        return self.request.get_argument(name, default=default)

    def get_arguments(self,
                      name: str,
                      default: list = None) -> Optional[list]:
        return self.request.get_arguments(name) or default

    def get_query_argument(self,
                           name: str,
                           default: Any = None) -> Optional[str]:
        return self.request.get_query_argument(name, default=default)

    def get_query_arguments(self,
                            name: str,
                            default: list = None) -> Optional[list]:
        return self.request.get_query_arguments(name) or default

    def get_from_header(self,
                        name: str,
                        default: Any = None) -> Optional[dict]:
        return self.request.request.headers.get(name, default)

    def get_from_cookie(self,
                        name: str,
                        default: Any = None) -> Optional[str]:
        return self.request.request.get_cookie(name, default=default)

    def get_body(self) -> Optional[str]:
        return self.request.request.body

    def translate(self, message: str) -> str:
        return self.request.locale.translate(message)


class HttpRequest:

    _instance_lock = threading.Lock()
    _request: BaseRequest = None

    @classmethod
    def configure(cls, *args, **kwargs) -> 'HttpRequest':
        if not hasattr(HttpRequest, '_instance'):
            with HttpRequest._instance_lock:
                if not hasattr(HttpRequest, '_instance'):
                    HttpRequest._instance = HttpRequest(*args, **kwargs)
        return HttpRequest._instance

    def set_request_proxy(self, request: BaseRequest):
        '''
        Set request proxy.

        usage:
            HttpRequest.configure().set_request_proxy(TornadoRequest)

        :param request: <BaseRequest>
        :return:
        '''
        self._request = request

    @property
    def request(self):
        if not self._request:
            self.set_request_proxy(TornadoRequest)
        return self._request
