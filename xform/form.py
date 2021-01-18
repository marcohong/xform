import types
from typing import Any, Awaitable, List, Union

from . import FormABC
from .fields import Field, Nested
from .binding import DataBinding
from .utils import FrozenDict

__all__ = ['Form', 'SubmitForm']

'''
Web request object.
e.g:
    Tornado: tornado.web.RequestHandler
'''
_REQUEST = 'Request'

FORM_TYPE_MAPS = FrozenDict({
    str: 'str',
    int: 'int',
    float: 'float',
    bool: 'bool',
    list: 'list'
})


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

    def __getattr__(self, key: str):
        return self.__fields__[key]

    async def _bind(self,
                    data: dict,
                    translate: callable = None
                    ) -> Awaitable[tuple]:
        ret, err, data = {}, {}, data or {}
        for name, field in self.__fields__.items():
            validate = await field._run_validate(data.get(name),
                                                 name,
                                                 data,
                                                 translate=translate)
            if not validate.is_valid:
                err[field.data_key] = validate.error
            else:
                ret[name] = validate.get_value()
        return ret, err

    async def bind(self,
                   request: _REQUEST,
                   locations: Union[tuple, str] = None) -> Awaitable[tuple]:
        '''Bind data from request.

        Bind data and check the accuracy of data.

        :param request: e.g: tornado.web.RequestHandler
        :param locations: `<uple/str>` form/json/query/headers/cookies

        :return: `<tuple>` (data, error)
        '''
        _bind = DataBinding(request, self.__fields__, locations=locations)
        data = await _bind.bind()
        return await self._bind(data, translate=_bind.translate)

    def dict_bind(self,
                  data: dict,
                  request: _REQUEST = None
                  ) -> Awaitable[tuple]:
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
        _data = DataBinding.dict_binding(self.__fields__, data)
        return self._bind(_data, translate=translate)

    def _fmt_detail(self, field: Field) -> dict:
        type_ = list if field.lst else (field.cvt_type or str)
        data = {
            'field': field.data_key,
            'type': type_,
            'type_str': FORM_TYPE_MAPS.get(type_, 'str'),
            'required': field.required,
            'length': field.length,
            'default': field.default,
            'description': field.description,
            'when_field': field.when_field,
            'when_value': field.when_value

        }
        if type_ in (int, float):
            data.update({'min': field._min, 'max': field._max})
        return data

    def _get_nested_details(self, nested: Nested) -> list:
        datas = []
        for _, field in nested.schema.__fields__.items():
            if isinstance(field, Nested):
                datas.extend(self._get_nested_details(field))
            else:
                datas.append(self._fmt_detail(field))
        return datas

    def get_field_details(self) -> List[dict]:
        '''
        Return field details

        :return: `<list>`
        '''
        datas = []
        for _, field in self.__fields__.items():
            if isinstance(field, Nested):
                datas.extend(self._get_nested_details(field))
            else:
                datas.append(self._fmt_detail(field))
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
        self.__slots = frozenset(['_filter', 'bind'])
        self.__form__ = None
        self.__fields__ = self._filter(kwargs)

    def _filter(self, fields: dict) -> dict:
        data = {}
        for key, field in fields.items():
            if isinstance(field, Field):
                data[key] = field
            elif key in self.__slots:
                raise KeyError(f'{key} is already defined')
            else:
                setattr(self, key, field)
        return data

    def __getattr__(self, key: str):
        assert self.__form__, \
            f'{self.__class__.__name__} form does not bind initial'
        return getattr(self.__form__, key)

    def bind(self,
             request: _REQUEST,
             locations: Union[str, tuple] = None) -> Awaitable[tuple]:
        '''Bind data from request.

        Bind data and check the accuracy of data.

        :param request: e.g: tornado.web.RequestHandler
        :param locations: `<uple/str>` form/json/query/headers/cookies

        :return: `<tuple>` (data, error)
        '''
        if not self.__form__:
            form = type('SubmitForm', (Form,), self.__fields__)
            self.__form__ = form()
        return self.__form__.bind(request, locations=locations)
