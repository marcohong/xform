import types
from typing import Any, Awaitable, List, Union

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
    '''
    Base form.

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

    def __init__(self, **kwargs: Any) -> None:
        for key, val in kwargs.items():
            if hasattr(self, key):
                raise ValueError('Key already exist.')
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

    async def bind(self,
                   request: _REQUEST,
                   locations: Union[tuple, str] = None) -> Awaitable[tuple]:
        '''Bind data from request.

        Bind data and check the accuracy of data.

        :param request: e.g: tornado.web.RequestHandler
        :param locations: `<uple/str>` form/json/query/headers/cookies
        :return: `<tuple>` (data, error)
        '''
        _bind = DataBinding(request,
                            self.__fields__,
                            locations=locations)
        data = _bind.bind()
        if isinstance(data, types.CoroutineType):
            data = await data
        return await self._bind(data, translate=_bind.translate)

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
        data = DataBinding.dict_binding(self.__fields__, data)
        return self._bind(data, translate=translate)

    def get_field_details(self) -> List[dict]:
        '''
        Return field details

        :return: `<list>`
        '''
        tmap = {
            str: 'str',
            int: 'int',
            float: 'float',
            bool: 'bool',
            list: 'list'
        }
        datas = []
        for _, field in self.__fields__.items():
            type_ = list if field.lst else (field.cvt_type or str)
            data = {
                'field': field.data_key,
                'type': type_,
                'type_str': tmap.get(type_, 'str'),
                'required': field.required,
                'length': field.length,
                'default': field.default,
                'description': field.description,
                'when_field': field.when_field,
                'when_value': field.when_value

            }
            if type_ in (int, float):
                data.update({'min': field._min, 'max': field._max})
            datas.append(data)
        return datas


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
        self.__fields__ = kwargs
        self.__form__ = None

    def __getattr__(self, key: str):
        try:
            return self.__fields__[key]
        except KeyError:
            raise AttributeError(f'SubmitForm object has not attribute {key}.')

    def bind(self,
             request: _REQUEST,
             locations: Union[str, tuple] = None) -> Awaitable[tuple]:
        if not self.__form__:
            form = type('SubmitForm', (Form,), self.__fields__)
            self.__form__ = form()
        return self.__form__.bind(request, locations=locations)

    def get_field_details(self) -> List[dict]:
        assert self.__form__
        return self.__form__.get_field_details()
