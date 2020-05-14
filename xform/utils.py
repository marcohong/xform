from typing import Any
try:
    import ujson as json
    JDecodeError = ValueError
except ImportError:
    import json
    JDecodeError = json.decoder.JSONDecodeError


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
