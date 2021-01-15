import threading

from xform.adapters import BaseRequest
from xform.adapters.tornado import TornadoRequest

__all__ = ['HttpRequest']


class HttpRequest:

    _instance_lock = threading.Lock()
    _request: BaseRequest = None

    @classmethod
    def configure(cls, request_proxy: BaseRequest = None) -> 'HttpRequest':
        if not hasattr(HttpRequest, '_instance'):
            with HttpRequest._instance_lock:
                if not hasattr(HttpRequest, '_instance'):
                    HttpRequest._instance = HttpRequest()
                if request_proxy and issubclass(request_proxy, BaseRequest):
                    HttpRequest._request = request_proxy
                else:
                    HttpRequest._request = TornadoRequest
        return HttpRequest._instance

    def set_request_proxy(self, request: BaseRequest):
        '''
        Set request proxy.

        usage::

            HttpRequest.configure().set_request_proxy(TornadoRequest)

        v0.2.2 'set_request_proxy' is deprecated.
        Use 'HttpRequest.configure(request_proxy=xxx)' set request proxy.

        :param request: `<BaseRequest>`
        :return:
        '''
        if not request or not issubclass(request, BaseRequest):
            raise ValueError('Request must be a subclass of BaseRequest')
        self._request = request

    @property
    def request(self):
        return self._request
