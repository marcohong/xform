'''
Binding request datas.

See the DataBinding class for more information.

'''
import types
from typing import Any, Awaitable, Dict, Optional, Union

from .httputil import HttpRequest, BaseRequest
from .utils import AttrDict, JsonDecodeError, json_loads
from .fields import Field, Nested

# Content-Type
IEME = AttrDict(
    MIME_HTML='text/html',
    MIME_XML='text/xml',
    MIME_PLAIN='text/plain',
    MIME_XML2='application/xml',
    MIME_JSON='application/json',
    MIME_FORM='application/x-www-form-urlencoded',
    MIME_MULTPART_FORM='multipart/form-data',
    MIME_YAML='application/x-yaml')


class Content:
    def __init__(self, req: BaseRequest, fields: dict) -> None:
        '''
        :param req: `<BaseRequest>` tornado/flask... request
        :param fields: `<dict>` {data_key:field_class}
        '''
        self.req = req
        self.fields = fields

    @staticmethod
    def is_coroutine(value: Any) -> bool:
        return isinstance(value, types.CoroutineType)

    def name(self) -> str:
        return 'form'

    def binding(self):
        raise NotImplementedError


class JsonContent(Content):
    '''
    Accept: application/json
    Content-Type: application/json(request payload, json data)
    '''

    def name(self) -> str:
        return 'json'

    async def binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        try:
            value = self.req.get_body()
            if self.is_coroutine(value):
                value = await value
            data = json_loads(value)
        except (JsonDecodeError, ValueError):
            data = None
        return data


class _KVContent(Content):
    def __init__(self, req: BaseRequest, fields: dict):
        super().__init__(req, fields)
        self.get_arg = None
        self.get_args = None
        self.initialize()

    def initialize(self):
        pass

    async def _get_nested(self, parent: str, nested: Nested):
        data = {}
        for name, field in nested.schema.__fields__.items():
            if isinstance(field, Nested):
                return self._get_nested(field.data_key, field)
            if field.lst is False:
                value = self.get_arg(
                    f'{parent}.{field.data_key}', default=None)
            else:
                value = self.get_args(f'{parent}.{field.data_key}')
            if self.is_coroutine(value):
                value = await value
            data[name] = value
        return data

    async def _binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        data = {}
        for name, field in self.fields.items():
            if isinstance(field, Nested):
                data[name] = await self._get_nested(field.data_key, field)
                continue
            if field.lst is False:
                value = self.get_arg(field.data_key, default=None)
            else:
                value = self.get_args(field.data_key)
            if self.is_coroutine(value):
                value = await value
            data[name] = value
        return data

    def binding(self) -> Awaitable[Optional[dict]]:
        '''
        :return: `<dict>` name:value
        '''

        return self._binding()


class FormContent(_KVContent):
    '''
    Accept: text/html
    Content-Type: application/x-www-form-urlencoded(form submit)
    Content-Type: multipart/form-data(file upload)
    '''

    def initialize(self):
        self.get_arg = self.req.get_argument
        self.get_args = self.req.get_arguments

    def name(self) -> str:
        return 'form'


class QueryContent(_KVContent):

    def initialize(self):
        self.get_arg = self.req.get_query_argument
        self.get_args = self.req.get_query_arguments

    def name(self) -> str:
        return 'query'


class _CHContent(_KVContent):
    async def _get_nested(self, parent: str, nested: Nested):
        data = {}
        for name, field in nested.schema.__fields__.items():
            if isinstance(field, Nested):
                return self._get_nested(field.data_key, field)
            if field.lst is False:
                value = self.get_arg(f'{parent}.{field.data_key}')
            else:
                value = [self.get_arg(f'{parent}.{field.data_key}')]
            if self.is_coroutine(value):
                value = await value
            data[name] = value
        return data

    async def _binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        data = {}
        for name, field in self.fields.items():
            if isinstance(field, Nested):
                data[name] = await self._get_nested(field.data_key, field)
                continue
            if field.lst is False:
                value = self.get_arg(field.data_key)
            else:
                value = [self.get_arg(field.data_key)]
            if self.is_coroutine(value):
                value = await value
            data[name] = value
        return data

    def binding(self) -> Awaitable[Optional[dict]]:
        '''
        :return: `<dict>` name:value
        '''

        return self._binding()


class CookiesContent(_CHContent):

    def initialize(self):
        self.get_arg = self.req.get_from_cookie

    def name(self) -> str:
        return 'cookies'


class HeadersContent(_CHContent):
    def initialize(self):
        self.get_arg = self.req.get_from_header

    def name(self) -> str:
        return 'headers'


LOCATIONS = dict(json=JsonContent,
                 query=QueryContent,
                 form=FormContent,
                 headers=HeadersContent,
                 cookies=CookiesContent)


class DataBinding:

    def __init__(self,
                 req: 'HttpRequest',
                 fields: Dict[str, Field],
                 locations: Union[str, tuple] = None) -> None:
        self.req = req
        _http = HttpRequest.configure()
        self.request = _http.request(req)
        self.fields = fields
        self.locations = locations
        self.content = None

    def _base_kwargs(self) -> dict:
        return dict(req=self.request, fields=self.fields)

    def _auto_configure(self) -> Content:
        kwds = self._base_kwargs()
        content_type = self.request.get_from_header('Content-Type', '').lower()
        _method = self.request.get_request_method()
        if _method.upper() == 'GET':
            self.content = QueryContent(**kwds)
        elif IEME.MIME_JSON in content_type:
            self.content = JsonContent(**kwds)
        elif IEME.MIME_FORM in content_type or \
                IEME.MIME_MULTPART_FORM in content_type:
            self.content = FormContent(**kwds)
        else:
            self.content = FormContent(**kwds)
        return self.content

    async def bind(self) -> Awaitable[Optional[dict]]:
        '''
        Data binding

        :return: `<dict>`
        '''
        if not self.locations:
            content = self._auto_configure()
            return await content.binding()

        if isinstance(self.locations, str):
            self.locations = (self.locations,)
        for location in self.locations:
            self.content = LOCATIONS.get(location)(**self._base_kwargs())
            data = self.content.binding()
            if data and Content.is_coroutine(data):
                data = await data
            if data:
                return data
        return None

    @staticmethod
    def dict_binding(fields: Dict[str, Field], data: dict) -> Optional[dict]:
        _data = {}
        for name, field in fields.items():
            value = data.get(field.data_key, None)
            if field.lst and isinstance(value, str):
                value = [value]
            _data[name] = value
        return _data

    def translate(self, message: str) -> str:
        '''
        Translation message

        :param message: `<str>`
        :return: `<str>`
        '''
        return self.request.translate(message)
