'''
Binding request datas.

See the DataBinding class for more information.

'''
from typing import Union, Optional

from .httputil import HttpRequest, BaseRequest
from .utils import AttrDict, JsonDecodeError, json_loads

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
        :param fields: `<dict>` {name:field_class/regular}
        '''
        self.req = req
        self.fields = fields

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

    def binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        try:
            data = json_loads(self.req.get_body())
        except (JsonDecodeError, ValueError):
            data = None
        return data


class FormContent(Content):
    '''
    Accept: text/html
    Content-Type: application/x-www-form-urlencoded(form submit)
    Content-Type: multipart/form-data(file upload)
    '''

    def name(self) -> str:
        return 'form'

    def binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        datas = {}
        for name, field in self.fields.items():
            if isinstance(field, str) or field.lst is False:
                value = self.req.get_argument(field.data_key, default=None)
            else:
                value = self.req.get_arguments(field.data_key)
            datas[name] = value
        return datas


class QueryContent(Content):

    def name(self) -> str:
        return 'query'

    def binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        datas = {}
        for name, field in self.fields.items():
            if isinstance(field, str) or field.lst is False:
                value = self.req.get_query_argument(field.data_key,
                                                    default=None)
            else:
                value = self.req.get_query_arguments(field.data_key)
            datas[name] = value
        return datas


class CookiesContent(Content):
    def name(self) -> str:
        return 'cookies'

    def binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        datas = {}
        cget = self.req.get_from_cookie
        for name, field in self.fields.items():
            if isinstance(field, str) or field.lst is False:
                value = cget(field.data_key)
            else:
                value = [cget(field.data_key)]
            datas[name] = value
        return datas


class HeadersContent(Content):
    def name(self) -> str:
        return 'headers'

    def binding(self) -> Optional[dict]:
        '''
        :return: `<dict>` name:value
        '''
        datas = {}
        hget = self.req.get_from_header
        for name, field in self.fields.items():
            if isinstance(field, str) or field.lst is False:
                value = hget(field.data_key)
            else:
                value = [hget(field.data_key)]
            datas[name] = value
        return datas


LOCATIONS = dict(json=JsonContent,
                 query=QueryContent,
                 form=FormContent,
                 headers=HeadersContent,
                 cookies=CookiesContent)


class DataBinding:

    def __init__(self,
                 req: 'HttpRequest',
                 fields: dict,
                 locations: Union[str, tuple] = None) -> None:
        self.req = req
        _http = HttpRequest.configure()
        self.request = _http.request(req)
        self.fields = fields
        self.locations = locations
        self.content = None

    def _base_kwargs(self) -> dict:
        return dict(req=self.request, fields=self.fields)

    def _auto_configure(self) -> None:
        kwds = self._base_kwargs()
        content_type = self.request.get_from_header('Content-Type', '')
        _method = self.request.get_request_method()
        if _method.upper() == 'GET' and not content_type:
            self.content = QueryContent(**kwds)
        elif IEME.MIME_JSON in content_type:
            self.content = JsonContent(**kwds)
        elif IEME.MIME_FORM in content_type or \
                IEME.MIME_MULTPART_FORM in content_type:
            self.content = FormContent(**kwds)
        else:
            self.content = FormContent(**kwds)

    def bind(self) -> Optional[dict]:
        '''
        Data binding

        :return: `<dict>`
        '''
        if not self.locations:
            self._auto_configure()
            return self.content.binding()

        if isinstance(self.locations, str):
            self.locations = (self.locations,)
        for location in self.locations:
            self.content = LOCATIONS.get(location)(**self._base_kwargs())
            data = self.content.binding()
            if data:
                return data
        return None

    @staticmethod
    def dict_binding(fields: dict, data: dict) -> Optional[dict]:
        _data = {}
        for name, field in fields.items():
            if isinstance(field, str) or field.lst is False:
                value = data.get(field.data_key, None)
            else:
                value = data.get(field.data_key, None)
                if isinstance(value, str):
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
