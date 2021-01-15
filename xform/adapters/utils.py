
import attr
from multidict import MultiDict, MultiDictProxy


@attr.s(auto_attribs=True, frozen=True, slots=True)
class ContentType:
    type: str
    subtype: str
    parameters: 'MultiDictProxy[str]'


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
