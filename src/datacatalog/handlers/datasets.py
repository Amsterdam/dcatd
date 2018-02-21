import re
import typing as T

from aiohttp import web


# _JSON_POINTER_SEGMENT = re.compile(
#     r'(/items)?(/properties)?([^/=~<>]+)'
# )
_FACET_QUERY_KEY = re.compile(
    r'(?:/properties/[^/=~<>]+(?:/items)?)+'
)
_FACET_QUERY_VALUE = re.compile(
    r'(in|eq|gt|lt|ge|le)=(.*)'
)
_COMMA_SEPARATED_SEGMENT = re.compile(
    r'(?:\\.|[^,\\])+'
)
_ESCAPED_CHARACTER = re.compile(r'\\(.)')


async def get(request: web.Request) -> web.Response:
    # language=rst
    """Handler for ``/datasets``"""
    query = request.query

    # Extract facet filters:
    filter = {}
    for key in query:
        if not _FACET_QUERY_KEY.fullmatch(key):
            continue
        if key not in filter:
            filter[key] = {}
        match = _FACET_QUERY_VALUE.fullmatch(query[key])
        if not match:
            raise web.HTTPBadRequest(
                "Unknown comparator in query parameter '%s'" % key
            )
        comparator = match[0]
        value = match[1]
        if comparator == 'in=':
            filter[key][comparator] = _split_comma_separated_stringset(value)
        else:
            filter[key][comparator] = value

    full_text_query = query.get('q')

    retval = web.Response()
    return retval


def _split_comma_separated_stringset(s: str) -> T.Optional[T.Set[str]]:
    pos = 0
    len_s = len(s)
    retval = set()
    while pos < len_s:
        if pos != 0 and s[pos] == ',':
            pos = pos + 1
        match = _COMMA_SEPARATED_SEGMENT.match(s, pos)
        if match is None:
            return None
        match = match[0]
        pos = pos + len(match)
        retval.add(_ESCAPED_CHARACTER.sub(r'\1', match))
    return retval


async def post(request: web.Request):
    ...
