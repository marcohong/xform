import re
import datetime
import time
import inspect
import types
from collections.abc import Iterable
from typing import Any, Tuple, Union, Optional

from tornado import httputil
from .validate import ValidationError, Validator
from . import FieldABC
from . import FormABC
from .utils import json_loads
from .messages import ErrMsg


VALUE_TYPES = Union[str, int, float]
ALL_TYPES = Union[str, int, float, bool, list, dict]


def is_generator(obj):
    return inspect.isgeneratorfunction(obj) or inspect.isgenerator(obj)


def is_iter_but_not_string(obj):
    return ((isinstance(obj, Iterable) and not hasattr(obj, 'strip'))
            or is_generator(obj))


class Field(FieldABC):

    cvt_type: callable = None

    def __init__(self,
                 *,
                 data_key: str = None,
                 required: bool = False,
                 default: Any = None,
                 length: Tuple[int, int] = None,
                 lst: bool = False,
                 validate: Any = None,
                 err_msg: str = None,
                 when_field: str = None,
                 when_value: Union[list, tuple] = None,
                 **kwargs: Any) -> None:
        '''
        :param data_key: <str> submit form parameters key, default field name
        :param required: <bool> True/False
        :param length: <tuple> tuple or list object, e.g: length=(0, 255)
        :param default: <Any> default None
        :param lst: <bool> list object ? default False
        :param validate: <Any> default None, callable/iterator/generator,
                        see class Validator
        :param err_msg: <dict> dict object: r->required, l->length, v->valid
                e.g:
                {
                    'required':'name is required.',
                    'length':'name exceeds the maximum length.',
                    'invalid':'name is invalid.'
                }
        :param when_field: <str> others params field
        :param when_value: <list/tuple> if field value in when_value,
            required is True
        :param kwargs: <dict> others params
        '''
        self.data_key = data_key
        self.required = required
        self.default = default
        self.length = length
        self.lst = lst
        self.when_field = when_field
        if when_field and (not when_value or
                           not isinstance(when_value, (list, tuple))):
            raise ValueError('when_value invalid, must be an array or tuple')
        self.when_value = when_value
        self.kwargs = kwargs
        self.null_values = (None, '',)
        self._value_is_null = False
        if validate is None:
            self.validators = []
        elif is_iter_but_not_string(validate):
            if not is_generator(validate):
                self.validators = validate
            else:
                self.validators = list(validate)
        elif callable(validate):
            self.validators = [validate]
        else:
            raise ValueError("The 'validate' parameter must be a callable "
                             'or a collection of callables.')
        self.validate = validate
        if hasattr(self, 'err_msg'):
            if err_msg:
                self.err_msg = {**self.err_msg, **err_msg}
        else:
            self.err_msg = err_msg or {}
        self.value = self.error = self.locale = None

    @property
    def is_valid(self):
        if self.error:
            return False
        return True

    def reset(self):
        self.value = self.error = self.locale = None

    def get_value(self):
        if self.is_valid:
            return self.value
        return self.default

    def get_defalut_value(self):
        if self.default and callable(self.default):
            self.value = self.default()
        else:
            self.value = self.default
        return self.value

    def value_to_string(self):
        if self.is_valid:
            return str(self.value)
        return None

    def set_error(self,
                  key: str,
                  default: str = ErrMsg.get_message('default_failed'),
                  *args: Any) -> None:
        '''
        Set error message.
        :param key: <str> err_msg key
        :param default: <str> default translation value
        :param args: only for default value format
        '''
        _msg = self.err_msg.get(key) or default
        if self.locale:
            _msg = self.locale(_msg)
        if args:
            _msg = _msg % args
        self.error = _msg

    async def _run_validate(self,
                            value: ALL_TYPES,
                            attr: str,
                            data: dict,
                            request: httputil.HTTPServerRequest = None
                            ) -> 'Field':
        '''
        Start running validate.

        :param value: <str/list> request value
        :param attr: <str> field name
        :param data: <dict> request datas
        :param request: <httputil.HTTPServerRequest>
        '''
        self.reset()
        self.locale = request.locale.translate if request else None
        self.value = value
        if self.lst:
            value = value if isinstance(value, (list, tuple)) else [value]
            not_null = False if not value else all([0 if x in (None, '')
                                                    else 1 for x in value])
            if not self._valid_required(value if not_null else ''):
                return self
            for val in value:
                if not isinstance(val, (str, int, float, bool)):
                    self.set_error('invalid')
                    return self
                if not self._valid_length(val):
                    return self
        elif isinstance(value, dict):
            if not self._valid_required(value):
                return self
        else:
            if not self._valid_required(value) or \
                    not self._valid_length(value):
                return self
        if self.when_field:
            if data.get(self.when_field) in self.when_value \
                    and self._value_is_null:
                self.set_error('invalid')
                return self
        return await self._abc_validate(value, attr, data)

    async def _abc_validate(self,
                            value: dict,
                            attr: str,
                            data: dict) -> 'Field':
        if self.required is False and self._value_is_null:
            self.get_defalut_value()
            return self
        ret = await self._validate(value, attr, data)
        if ret is not None:
            self.value = ret
        if not self.error and self.validators:
            await self._validator(value)
        return self

    def _valid_required(self, value: VALUE_TYPES) -> bool:
        self._value_is_null = value in self.null_values
        if self._value_is_null and self.required is True:
            self.set_error('required', ErrMsg.get_message('default_required'))
            return False
        return True

    def _valid_length(self, value: VALUE_TYPES) -> bool:
        if self.required is False and value in self.null_values:
            if self.default in self.null_values \
                    or isinstance(self.default, bool):
                return True
            self.get_defalut_value()
            value = str(self.value)
        else:
            value = f'{value}'

        if self.length is not None:
            if isinstance(self.length, tuple):
                if value is None or \
                        not (self.length[0] <= len(value) <= self.length[1]):
                    _msg = ErrMsg.get_message('default_length')
                    self.set_error('length',
                                   _msg,
                                   self.length[0],
                                   self.length[1])
                    return False
            elif isinstance(self.length, int):
                if value is None or len(value) != self.length:
                    _msg = ErrMsg.get_message('default_length_equal')
                    self.set_error('length', _msg, self.length)
                    return False
            else:
                return False
        return True

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[Any]:
        '''
        User-defined validation function.

        If the return value is the return value, otherwise the value
        '''
        pass

    async def _validator(self, value: VALUE_TYPES) -> None:
        for validate in self.validators:
            try:
                if self.cvt_type and value is not None:
                    try:
                        value = self.cvt_type(value)
                    except ValueError:
                        pass
                ret = validate(value)
                if isinstance(ret, types.CoroutineType):
                    await ret
                if not isinstance(validate, Validator) and ret is False:
                    self.set_error(
                        'invalid', ErrMsg.get_message('default_failed'))
            except ValidationError as verr:
                self.value = None
                if self.required is True:
                    self.set_error('invalid', verr.message)


class Number(Field):

    regex = r'\d+$|^\d+\.\d+$'
    cvt_type = float
    err_msg = {
        'invalid': ErrMsg.get_message('default_invalid'),
        'min_invalid': ErrMsg.get_message('min_invalid'),
        'max_invalid': ErrMsg.get_message('max_invalid')
    }

    def __init__(self,
                 *,
                 required: bool = True,
                 _min: Union[int, float] = None,
                 _max: Union[int, float] = None,
                 **kwargs: Any):
        self._min = _min
        self._max = _max
        kwargs['required'] = required
        super().__init__(**kwargs)

    def get_value(self):
        if self.is_valid:
            if self.value not in self.null_values and self.cvt_type:
                return self.cvt_type(self.value)
            return self.value
        return self.default

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[int]:
        if isinstance(value, bool):
            return self.default
        if isinstance(value, (int, float)):
            value = f'{value}'
        ret = re.match(self.regex, value)
        if not ret:
            self.set_error('invalid')
        else:
            if self._min is not None:
                if not self._compare_value(value, self._min):
                    self.set_error('min_invalid', None, self._min)
                    return self.default
            elif self._max is not None:
                if not self._compare_value(value, self._max):
                    self.set_error('max_invalid', None, self._max)
                    return self.default
            return value

    def _compare_value(self,
                       value: VALUE_TYPES,
                       cval: Union[int, float]) -> bool:
        _val = int(value) if value.isdigit() else float(value)
        return _val >= cval


class Integer(Number):

    regex = r'^0$|^[-1-9]\d*$'
    cvt_type = int


class Float(Number):
    regex = r'^\d+\.\d+$'
    cvt_type = float


class Str(Field):
    cvt_type = str

    def __init__(self, *, length: tuple = (0, 255), **kwargs: Any):
        kwargs['length'] = length
        super().__init__(**kwargs)

    def get_value(self):
        if self.is_valid and self.value is not None:
            if self.cvt_type:
                return self.cvt_type(self.value)
            return self.value
        return self.default


class EnStr(Str):

    letters = r'^[a-zA-Z]+$'
    upper = r'^[A-Z]+$'
    lower = r'^[a-z]+$'
    en_str = r'^[a-zA-Z0-9_!$@.#*&~^]+$'
    letters_digit = r'^\w+$'
    err_msg = {
        'invalid': ErrMsg.get_message('default_invalid')
    }

    def __init__(self,
                 *,
                 vtype: str = letters,
                 length: tuple = (0, 255),
                 **kwargs: Any):
        self.regex = vtype
        kwargs['length'] = length
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        ret = re.match(self.regex, value)
        if not ret:
            self.set_error('invalid')


class Raw(Field):
    pass


class Nested(Field):
    err_msg = {'type': ErrMsg.get_message('invalid_type')}

    def __init__(self,
                 nested: Any,
                 required: bool = False,
                 **kwargs: Any):
        self.nested = nested
        kwargs['required'] = required
        super().__init__(**kwargs)

    @property
    def schema(self):
        if callable(self.nested) and isinstance(self.nested, type):
            nested = self.nested()
        else:
            nested = self.nested
        if not isinstance(nested, FormABC):
            raise ValueError('Invalid type')
        return nested

    async def _run_validate(self,
                            value: Union[str, dict],
                            attr: str,
                            data: dict,
                            request: httputil.HTTPServerRequest
                            ) -> "Field":
        self.reset()
        self.locale = request.locale.translate
        self.value = value
        if not self._valid_required(value):
            return self
        if self.required is False and self._value_is_null:
            self.get_defalut_value()
            return self
        try:
            data = json_loads(value) if isinstance(value, str) else value
        except (ValueError, AssertionError):
            self.set_error('invalid')
        datas, errors = await self.schema.dict_bind(data, request)
        if errors:
            self.error = errors
        else:
            self.value = datas
        return self


class List(Field):
    err_msg = {
        'invalid': ErrMsg.get_message('default_invalid'),
        'too_less_error': ErrMsg.get_message('too_less_error'),
        'too_long_error': ErrMsg.get_message('too_long_error')
    }

    def __init__(self,
                 min_len: int = 1,
                 max_len: Union[None, int] = None,
                 data_type: callable = None,
                 length: Union[int, tuple] = None,
                 **kwargs: Any):
        kwargs['lst'] = True
        kwargs['length'] = length
        self._data_type = data_type
        self._min_len = min_len
        self._max_len = max_len or 0
        super().__init__(**kwargs)

    async def _validate(self,
                        value: list,
                        attr: str,
                        data: dict) -> Optional[list]:
        if len(value) < self._min_len:
            self.set_error('too_less_error', None, self._min_len)
            return
        if self._max_len > 0 and len(value) > self._max_len:
            self.set_error('too_long_error', None, self._max_len)
            return
        if self._data_type and callable(self._data_type):
            try:
                data = [self._data_type(i) for i in value]
                if not all(data):
                    raise ValueError
            except ValueError:
                self.set_error('invalid')
                return
            return data


class IntList(List):
    def __init__(self, dedup: bool = True, **kwargs):
        self.dedup = dedup
        kwargs['data_type'] = int
        super().__init__(**kwargs)

    def get_value(self):
        if self.is_valid:
            if isinstance(self.value, list):
                data = [int(i) for i in self.value if
                        isinstance(i, int) or i.isdigit()]
            else:
                data = [self.value] if self.value else []
            return list(set(data)) if self.dedup else data
        return self.default


class Boolean(Field):
    real = ('t', 'true', 'on', 'y', 'yes', '1', 1, True)
    fake = ('f', 'false', 'off', 'n', 'no', '0', 0, False)
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_bool')
    }

    def __init__(self,
                 *,
                 real: Union[list, tuple] = None,
                 fake: Union[list, tuple] = None,
                 **kwargs: Any):
        if real is not None:
            self.real = tuple(set(real))
        if fake is not None:
            self.fake = tuple(set(fake))
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[bool]:
        if not isinstance(value, (str, int, bool)):
            self.set_error('invalid')
            return
        elif isinstance(value, (int, bool)):
            return bool(value)
        elif value.lower() in self.real:
            return True
        elif value.lower() in self.fake:
            return False
        self.set_error('invalid')


class Timestamp(Integer):
    def __init__(self, length: int = 10, **kwargs: Any):
        kwargs['length'] = length
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        try:
            date = time.strftime('%Y-%m-%d %H:%M:%S',
                                 time.localtime(int(value)))
            datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            return int(value)
        except ValueError:
            self.set_error('invalid')


class DateTime(Field):
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_datetime')
    }

    def __init__(self, *,
                 fmt: str = '%Y-%m-%d %H:%M:%S',
                 convert: bool = False,
                 default: Union[callable, str] = None,
                 **kwargs: Any):
        self.fmt = fmt
        self.convert = convert
        kwargs['default'] = default
        super().__init__(**kwargs)

    @classmethod
    def _vaild(cls, value: VALUE_TYPES, fmt: str):
        try:
            res = datetime.datetime.strptime(value, fmt).strftime(fmt)
            if value != res:
                raise ValueError
            return True
        except ValueError:
            return False

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        try:
            # valid value regex
            if self._vaild(self.value, self.fmt) is False:
                raise ValueError
            if self.convert is True:
                date = datetime.datetime.strptime(value, self.fmt)
                return date
            return value
        except (TypeError, AttributeError, ValueError):
            eg_val = datetime.datetime.now().strftime(self.fmt)
            self.set_error('invalid', None, value, eg_val)


class Date(DateTime):
    def __init__(self,
                 fmt: str = '%Y-%m-%d',
                 **kwargs: Any):
        kwargs['fmt'] = fmt
        super().__init__(**kwargs)


class StartDate(Date):
    pass


class EndedDate(Date):
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_start_date')
    }

    def __init__(self, start_field: str, **kwargs: Any):
        self.start_field = start_field
        super().__init__(**kwargs)

    def _fmt_date(self, value: VALUE_TYPES) -> Optional[datetime.datetime]:
        try:
            return datetime.datetime.strptime(value, self.fmt)
        except ValueError:
            return None

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        if not data.get(self.start_field):
            self.set_error('invalid')
        else:
            start = self._fmt_date(data[self.start_field])
            ended = self._fmt_date(value)
            if start and ended and (ended >= start):
                return value
            self.set_error('invalid')


class Time(Field):
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_timestamp')
    }

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        if not value.isdigit():
            self.set_error('invalid', None, value)
        else:
            try:
                time.localtime(int(value))
                return int(self.value)
            except (ValueError, TypeError):
                self.set_error('invalid', None, value)


class Url(Str):

    default_schemes = {'http', 'https', 'ftp', 'ftps'}
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_url')
    }

    def __init__(self,
                 *,
                 relative: bool = False,
                 schemes: str = None,
                 require_tld: bool = True,
                 **kwargs) -> None:
        self.relative = relative
        self.require_tld = require_tld
        self.schemes = schemes or self.default_schemes
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        if '://' in value:
            scheme = value.split("://")[0].lower()
            if scheme not in self.schemes:
                self.set_error('invalid')
                return

        regex = self._regex_generator(self.relative, self.require_tld)
        if not regex.search(value):
            self.set_error('invalid')

    def _regex_generator(self, relative, require_tld):
        return re.compile(
            r"".join((
                r"^",
                r"(" if relative else r"",
                # scheme is validated separately
                r"(?:[a-z0-9\.\-\+]*)://",
                r"(?:[^:@]+?(:[^:@]*?)?@|)",  # basic auth
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+",
                r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|",  # domain...
                r"localhost|",  # localhost...
                (r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.?)|"
                 if not require_tld else r""),  # allow dotless hostnames
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|",  # ...or ipv4
                r"\[[A-F0-9]*:[A-F0-9:]+\])",  # ...or ipv6
                r"(?::\d+)?",  # optional port
                r")?" if relative else
                r"",  # host is optional, allow for relative URLs
                r"(?:/?|[/?]\S+)$",
            )),
            re.IGNORECASE,
        )


class Email(Str):
    regex = r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$'
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_email')
    }

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        ret = re.match(self.regex, value)
        if not ret:
            self.set_error('invalid')


class Phone(Number):
    regex = r'0?(13|14|15|16|17|18|19)[0-9]{9}'
    cvt_type = str
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_phone')
    }

    def __init__(self, *, length: int = 11, **kwargs: Any):
        self._min = None
        self._max = None
        kwargs.update({'length': length})
        super().__init__(**kwargs)


class IDCard(Str):
    len18 = (r"(?:1[1-5]|2[1-3]|3[1-7]|4[1-6]|5[0-4]|6[1-5])\d{4}(?:1[89]|20)"
             r"\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}(?:\d|[xX])")
    len15 = (r"(?:1[1-5]|2[1-3]|3[1-7]|4[1-6]|5[0-4]|6[1-5])\d{4}"
             r"\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}")

    err_msg = {
        'invalid': ErrMsg.get_message('invalid_idcard')
    }

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        ret = re.match(self.len18, value)
        ret2 = re.match(self.len15, value)
        if not ret and not ret2:
            self.set_error('invalid')
        else:
            return value


class Username(Str):
    regex = r'^[a-zA-Z][a-zA-Z0-9_]{%d,%d}$'
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_username')
    }

    def __init__(self, *,
                 regex: str = regex,
                 length: tuple = (3, 32),
                 **kwargs: Any):
        kwargs['length'] = length
        self._regex = regex
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        if isinstance(self.length, int):
            length = (self.length - 1, self.length - 1)
        else:
            length = (self.length[0] - 1, self.length[1] - 1)
        ret = re.match(self._regex % length, value)
        if not ret:
            self.set_error('invalid')


class Password(Str):
    regex = r'^([a-zA-Z0-9_!$@.#*&~^]){%d,%d}$'
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_password')
    }

    def __init__(self,
                 *,
                 regex: str = regex,
                 length: tuple = (0, 32),
                 **kwargs: Any):
        kwargs['length'] = (0, 256)
        self._length = length
        self._regex = regex
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        ret = re.match(self._regex % self._length, value)
        if not ret:
            self.set_error('invalid')
        else:
            return value


class Order(Str):
    '''
    Sql order columns

    e.g: id asc,time desc / time desc
    '''

    def __init__(self, _in: Union[list, tuple], **kwargs):
        self.columns = list(set(_in))
        kwargs['length'] = None
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        _value = []
        _exist_key = {}
        for item in value.split(','):
            key = item.split()[0]
            if key in _exist_key:
                continue
            _value.append(item.split())
            _exist_key[key] = True

        value = []
        for item in _value:
            if len(item) < 3 and \
                ((len(item) == 2 and item[-1] in ('asc', 'desc'))
                 ) and (self.columns and item[0] in self.columns):
                value.append(item)
            elif len(item) == 1:
                item.append('desc')
                value.append(item)
        value = ','.join([' '.join(item) for item in value])
        return value


class IpAddr(Str):
    ipv4 = (r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)"
            r"{3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    ipv6 = r'^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$'
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_ip')
    }

    def __init__(self, *,
                 length: tuple = (8, 32),
                 **kwargs: Any):
        kwargs['length'] = length
        super().__init__(**kwargs)

    async def _validate(self,
                        value: VALUE_TYPES,
                        attr: str,
                        data: dict) -> Optional[str]:
        ret = re.match(self.ipv4, value)
        ret2 = re.match(self.ipv6, value)
        if not ret and not ret2:
            self.set_error('invalid')
        else:
            return value


class Jsonify(Str):
    err_msg = {
        'invalid': ErrMsg.get_message('invalid_json')
    }

    def __init__(self, **kwargs: Any):
        kwargs['length'] = None
        super().__init__(**kwargs)

    def get_value(self):
        if self.is_valid and self.value is not None:
            return self.value
        return self.default

    async def _validate(self,
                        value: Union[str, dict],
                        attr: str,
                        data: dict) -> Optional[dict]:
        try:
            if isinstance(value, dict):
                data = value
            else:
                data = json_loads(value)
            assert isinstance(data, (list, dict))
            return data
        except (ValueError, AssertionError):
            self.set_error('invalid')
