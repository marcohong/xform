'''
Binding request datas.

See the RequestData class for more information.

'''
from typing import Optional, Union
from tornado import httputil

from .utils import AttrDict

'''
Content-Type:
    text/html
    text/xml
    text/plain
    application/xml
    application/json
    application/x-www-form-urlencoded
    multipart/form-data
    application/x-yaml
'''

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
    def __init__(self, req: httputil.HTTPServerRequest, fields: dict) -> None:
        '''
        :param req: <tornado.httputil.HTTPServerRequest> tornado request
        :param fields: <dict> {name:field_class/regular}
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
        :return: <dict> name:value
        '''
        return self.req.get_request_body(loads=True)


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
        :return: <dict> name:value
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
        :return: <dict> name:value
        '''
        datas = {}
        for name, field in self.fields.items():
            if isinstance(field, str) or field.lst is False:
                value = self.req.get_query_arguments(field.data_key)
            else:
                value = self.req.get_query_argument(field.data_key,
                                                    default=None)
            datas[name] = value
        return datas


class CookiesContent(Content):
    def name(self) -> str:
        return 'cookies'

    def binding(self) -> Optional[dict]:
        '''
        :return: <dict> name:value
        '''
        datas = {}
        cget = self.req.get_cookie
        for name, field in self.fields.items():
            if isinstance(field, str) or field.lst is False:
                value = [cget(field.data_key)]
            else:
                value = cget(field.data_key)
            datas[name] = value
        return datas


class HeadersContent(Content):
    def name(self) -> str:
        return 'headers'

    def binding(self) -> Optional[dict]:
        '''
        :return: <dict> name:value
        '''
        datas = {}
        hget = self.req.request.headers.get
        for name, field in self.fields.items():
            if isinstance(field, str) or field.lst is False:
                value = hget(field.data_key)
                if isinstance(value, str):
                    value = [value]
            else:
                value = hget(field.data_key)
            datas[name] = value
        return datas


class RequestData:
    '''
    Binding request datas.

    usage:
        datas = RequestData(req,fields).bind()

        or

        rd = RequestData(req,fields)
        print(rd.name())
        datas = rd.bind()

    '''
    __location_map__ = {
        'json': JsonContent,
        'query': QueryContent,
        'form': FormContent,
        'headers': HeadersContent,
        'cookies': CookiesContent
    }

    default_content = FormContent

    def __init__(self,
                 req: httputil.HTTPServerRequest,
                 fields: dict,
                 locations: Union[str, tuple] = None) -> None:
        '''
        :param req: <tornado.httputil.HTTPServerRequest> tornado request
        :param fields: <dict> {name:field_class/regular}
        :param locations: <str/tuple> json/query/form/headers/cookies
        '''
        self.req = req
        self.fields = fields
        self.locations = locations
        self.content = None
        self.accept = req.request.headers.get('Accept')
        self.content_type = req.request.headers.get('Content-Type',
                                                    IEME.MIME_FORM)

    def _base_data(self):
        return dict(req=self.req, fields=self.fields)

    def configure(self) -> None:
        kwds = self._base_data()
        if IEME.MIME_JSON in self.content_type:
            self.content = JsonContent(**kwds)
        elif IEME.MIME_FORM in self.content_type:
            self.content = FormContent(**kwds)
        elif IEME.MIME_MULTPART_FORM in self.content_type:
            self.content = FormContent(**kwds)
        else:
            self.content = FormContent(**kwds)

    def bind(self) -> Optional[dict]:
        if self.locations:
            if isinstance(self.locations, str):
                self.locations = (self.locations,)
            for location in self.locations:
                self.content = self.__location_map__.get(
                    location)(**self._base_data())
                data = self.content.binding()
                if data:
                    return data
            return None
        else:
            self.configure()
            return self.content.binding()
