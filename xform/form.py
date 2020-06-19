'''
Form submission verification class.

usage::

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
import types
from typing import Any, Union

from . import FormABC
from .fields import Field
from .binding import DataBinding

__all__ = ['Form', 'SubmitForm']

'''
Web request object.
e.g:
    Tornado: tornado.web.RequestHandler
'''
_REQUEST = 'Request'


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
                    translate: callable = None
                    ) -> tuple:
        _errors, _datas = {}, {}
        data = data or {}
        for name, field in self.__fields__.items():
            value = data.get(name)
            validate = await field._run_validate(value,
                                                 name,
                                                 data,
                                                 translate=translate)
            if not validate.is_valid:
                _errors[field.data_key] = validate.error
            setattr(self, name, validate.get_value())
            _datas[name] = validate.get_value()
        return _datas, _errors

    def bind(self,
             request: _REQUEST,
             locations: Union[tuple, str] = None) -> tuple:
        '''Bind data from request.

        Bind data and check the accuracy of data.

        :param request: e.g: tornado.web.RequestHandler
        :param locations: `<uple/str>` form/json/query/headers/cookies
        :return: `<tuple>` (data, error)
        '''
        _bind = DataBinding(request,
                            self.__fields__,
                            locations=locations)
        return self._bind(_bind.bind(), translate=_bind.translate)

    def dict_bind(self,
                  data: dict,
                  request: _REQUEST = None
                  ) -> tuple:
        '''Check the accuracy of data.

        :param data: `<dict>`
        :param request: e.g: tornado.web.RequestHandler
        :return: `<tuple>` (data, error)
        '''
        translate: callable = None
        if request:
            if isinstance(request, (types.FunctionType, types.MethodType)):
                translate = request
            else:
                _bind = DataBinding(request, data)
                translate = _bind.translate
        return self._bind(data, translate=translate)


class SubmitForm:
    '''
    Create simple submit form.

    useage::

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
             request: _REQUEST,
             locations: Union[str, tuple] = None) -> tuple:
        if not self.__form__:
            form = type('SubmitForm', (Form,), self.__fields__)
            self.__form__ = form()
        return self.__form__.bind(request, locations=locations)
