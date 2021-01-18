from functools import lru_cache
from typing import Any
try:
    import ujson as json
    JDecodeError = ValueError
except ImportError:
    import json
    JDecodeError = json.decoder.JSONDecodeError
import attr
from multidict import MultiDict, MultiDictProxy


class JsonDecodeError(JDecodeError):
    pass


def json_dumps(value: Any, sort_keys=None) -> str:
    return json.dumps(value, sort_keys=sort_keys)


def json_loads(value: Any) -> Any:
    return json.loads(value)


class AttrDict(dict):
    '''
    Dictionary subclass enabling attribute lookup/assignment of keys/values.

    For example::

        >>> m = AttrDict({'foo': 'bar'})
        >>> m.foo
        'bar'
        >>> m.foo = 'not bar'
        >>> m['foo']
        'not bar'
    '''

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = value


class FrozenDict(dict):
    def __setitem__(self, key: Any, value: Any):
        raise TypeError('Dictionary can not be modified')


@attr.s(auto_attribs=True, frozen=True, slots=True)
class ContentType:
    type: str
    subtype: str
    parameters: 'MultiDictProxy[str]'


@lru_cache(50)
def parse_content_type(ctype: str) -> str:
    parts = ctype.split(';')
    params = MultiDict()
    for item in parts[1:]:
        if not item:
            continue
        key, value = item.split('=', 1) if '=' in item else (item, '')
        params.add(key.lower().strip(), value.strip(' "'))
    fulltype = parts[0].strip().lower()
    if fulltype == '*':
        fulltype = '*/*'
    mtype, stype = fulltype.split(
        '/', 1) if '/' in fulltype else (fulltype, '')
    return ContentType(type=mtype, subtype=stype, parameters=params)
