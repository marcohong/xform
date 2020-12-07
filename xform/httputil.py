import threading

from xform.adapters import BaseRequest
from xform.adapters.tornado import TornadoRequest

__all__ = ['HttpRequest']


class HttpRequest:

    _instance_lock = threading.Lock()
    _request: BaseRequest = None

    @classmethod
    def configure(cls) -> 'HttpRequest':
        if not hasattr(HttpRequest, '_instance'):
            with HttpRequest._instance_lock:
                if not hasattr(HttpRequest, '_instance'):
                    HttpRequest._instance = HttpRequest()
        return HttpRequest._instance

    def set_request_proxy(self, request: BaseRequest):
        '''
        Set request proxy.

        usage::

            HttpRequest.configure().set_request_proxy(TornadoRequest)

        :param request: `<BaseRequest>`
        :return:
        '''
        self._request = request

    @property
    def request(self):
        if not self._request:
            self.set_request_proxy(TornadoRequest)
        return self._request
