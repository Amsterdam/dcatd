import logging
import typing as T
import re

from aiohttp import web

_logger = logging.getLogger(__name__)


_REQ_ETAG_STAR_TYPE = T.NewType('EtagStar', str)
REQ_ETAG_STAR = _REQ_ETAG_STAR_TYPE('*')
""" An Etag value of `*`. """

REQ_ETAG_TYPE = T.Union[None, _REQ_ETAG_STAR_TYPE, T.Set[str]]
""" An Etag value in a conditional request header is translated into one of the following values:

- `None`: No Etag given
- `*`: Etag value is a star
- `set(str, ...)`: One or more Etag strings
"""

_ETAGS_PATTERN = re.compile(
    r'\s*(?:W/)?"[\x21\x23-\x7e\x80-\xff]+"(?:\s*,\s*(?:W/)?"[\x21\x23-\x7e\x80-\xff]+")*'
)
_ETAG_ITER_PATTERN = re.compile(
    r'((?:W/)?"[\x21\x23-\x7e\x80-\xff]+")'
)

_ConditionalHeaderType = T.NewType('ConditionalHeader', str)
HEADER_IF_MATCH = _ConditionalHeaderType('If-Match')
HEADER_IF_NONE_MATCH = _ConditionalHeaderType('If-None-Match')


def parse_if_header(request: web.Request, header: _ConditionalHeaderType) -> REQ_ETAG_TYPE:
    # language=rst
    """Parses ``If-(None-)Match:`` request headers.

    Args:
        request:
        header:  either ``HEADER_IF_MATCH`` or ``HEADER_IF_NONE_MATCH``

    Returns:
        REQ_ETAG_TYPE

    Raises:
        web.HTTPBadRequest: If the request header is malformed.

    Warning:
        This parser allows an ``If-(None-)Match:`` request header with an empty
        value.  This is not :rfc:`7232` compliant, and a work-around for a bug
        in Swagger-UI.

    """
    if header not in request.headers:
        return None

    # The startswith is used to remove a potentially added W/ (weak reference)
    # to the E-tag by a load balancer like HAproxy.
    # This prevents a 412 HTTP error when the W/ is added by the HAproxy but
    # compaired with the identical value without the W/ addition and causes
    # the 412 HTTP error:
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/412
    header_value = ','.join( header[2:] if header.startswith(('W/', 'w/')) else header for header in request.headers.getall(header) )
    if header_value == '':
        return None
    if header_value == REQ_ETAG_STAR:
        return REQ_ETAG_STAR
    if not _ETAGS_PATTERN.fullmatch(header_value):
        raise web.HTTPBadRequest(
            text="Syntax error in request header {}: {}".format(header, header_value)
        )
    return {match[1] for match in _ETAG_ITER_PATTERN.finditer(header_value)}


def match_etags(etag: str, etags: T.Iterable[str], allow_weak: bool) -> bool:
    # language=rst
    """ETag comparison according to :rfc:`7232`.

    See :rfc:`section 2.3.2 <7232#section-2.3.2>` for a detailed explanation of
    *weak* vs. *strong comparison*.

    Parameters:
        etag:
        etags:
        allow_weak: if ``True``, this function uses the *weak comparison*
            algorithm;  otherwise *strong comparison* is used.

    Returns:
        ``True`` if ``etag`` matches against any ETag in ``etags``.

    """
    if not allow_weak:
        return str(etag)[0] == '"' and etag in etags
    if etag[0:2] == 'W/':
        etag = etag[2:]
    return etag in etags or ('W/' + etag) in etags
