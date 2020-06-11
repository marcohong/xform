'''
Form submission verification class.

usage:
    class UserForm(Form):
        id = Integer(required=True)
        name = Field(required=True, length=(1, 3))
        age = Field(required=True)
        sex = Field(validate=OneOf(('man', 'women')))

    user = UserForm()
    datas, errors = await user.bind(self.request)
    print(errors)
    print(datas)

'''
from typing import Any, Union
from tornado import httputil

from . import FormABC
from .fields import Field
from .binding import RequestData

__all__ = ['Form', 'SubmitForm']


class FormMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict):
        # meta = attrs.get('Meta')
        if name == 'Form':
            return super().__new__(cls, name, bases, attrs)
        fields = {}
        for fname, fvalue in attrs.items():
            if isinstance(fvalue, Field):
                fields[fname] = fvalue
                if not fvalue.data_key:
                    fvalue.data_key = fname

        # delete attrs field
        for key, _ in fields.items():
            del attrs[key]
        attrs['__fields__'] = fields
        return super().__new__(cls, name, bases, attrs)


class Form(FormABC, metaclass=FormMeta):
    def __init__(self, **kwargs: Any) -> None:
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f'Form object has not attribute {key}.')

    async def _bind(self,
                    data: dict,
                    request: httputil.HTTPServerRequest = None
                    ) -> tuple:
        _errors, _datas = {}, {}
        for name, field in self.__fields__.items():
            value = data.get(name)
            validate = await field._run_validate(value,
                                                 name,
                                                 data,
                                                 request=request)
            if not validate.is_valid:
                _errors[field.data_key] = validate.error
            setattr(self, name, validate.get_value())
            _datas[name] = validate.get_value()
        return _datas, _errors

    def bind(self,
             request: httputil.HTTPServerRequest,
             locations: Union[tuple, str] = None) -> tuple:
        '''Bind data from request.

        Bind data and check the accuracy of data.

        :param request: <httputil.HTTPServerRequest>
        :param locations: <uple/str> form/json/query/headers/cookies
        :return: <tuple> (data, error)
        '''
        kwds = RequestData(request,
                           self.__fields__,
                           locations=locations).bind()
        return self._bind(kwds, request)

    def dict_bind(self,
                  data: dict,
                  request: httputil.HTTPServerRequest = None
                  ) -> tuple:
        '''Check the accuracy of data.

        :param data: <dict>
        :param request: <httputil.HTTPServerRequest>
        :return: <tuple> (data, error)
        '''
        return self._bind(data, request)


class SubmitForm:
    '''
    Create simple submit form.

    useage:

        form = SubmitForm(
            id = Integer(required=True)
            name = Field(required=True, length=(1, 3))
            age = Field(required=False, default=18)
        )
        data, error = form.bind(request)
        print(data)
    '''

    def __init__(self, **kwargs: Any):
        self.__fields__ = {}
        self.__form__ = None
        for key, val in kwargs.items():
            setattr(self, key, val)
            self.__fields__[key] = val

    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f'SubmitForm object has not attribute {key}.')

    def bind(self,
             request: httputil.HTTPServerRequest,
             locations: Union[str, tuple] = None) -> tuple:
        if not self.__form__:
            form = type('SubmitForm', (Form,), self.__fields__)
            self.__form__ = form()
        return self.__form__.bind(request, locations=locations)
