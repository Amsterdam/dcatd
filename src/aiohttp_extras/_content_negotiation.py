# language=rst
"""

To support *content type negotiation* in GET requests, this package provides the
:meth:`@produces_content_types <produces_content_types>` decorator.

"""
import logging
import functools
import typing as T

from aiohttp import web, hdrs

_logger = logging.getLogger(__name__)

_BCT_CACHED_VALUE_KEY = 'aiohttp_extras.best_content_type'


def _best_content_type(request: web.Request,
                       available_content_types: T.List[str]) -> str:
    # language=rst
    """The best matching content type.

    Returns:
        The best content type to use for the HTTP response, given a certain
        ``request`` and a list of ``available_content_types``.

    Parameters:
        request (aiohttp.web.Request): the current request
        available_content_types: an ordered list of available content types,
            ordered by quality, best quality first.

    Raises:
        web.HTTPNotAcceptable: if none of the available content types are
            acceptable by the client. See :ref:`aiohttp web exceptions
            <aiohttp-web-exceptions>`.

    Example::

        AVAILABLE = [
            'foo/bar',
            'foo/baz; charset="utf-8"'
        ]
        def handler(request):
            bct = best_content_type(request, AVAILABLE)

    """
    if hdrs.ACCEPT not in request.headers:
        return available_content_types[0]
    accept = ','.join(request.headers.getall(hdrs.ACCEPT))
    acceptable_content_types = dict()
    for acceptable in accept.split(','):
        try:
            main, sub = acceptable.split(';', 2)[0].strip().split('/', 2)
        except ValueError:
            raise web.HTTPBadRequest(text="Malformed Accept: header") from None
        if main not in acceptable_content_types:
            acceptable_content_types[main] = set()
        acceptable_content_types[main].add(sub)
    # Try to find a matching 'main/sub' or 'main/*':
    for available in available_content_types:
        main, sub = available.split(';', 2)[0].strip().split('/', 2)
        if main in acceptable_content_types:
            subs = acceptable_content_types[main]
            if sub in subs or '*' in subs:
                return available
    if '*' in acceptable_content_types and '*' in acceptable_content_types['*']:
        return available_content_types[0]
    # Darn, none of our content types are acceptable to the client:
    body = ",".join(available_content_types).encode('ascii')
    raise web.HTTPNotAcceptable(
        body=body,
        content_type='text/plain; charset="US-ASCII"'
    )


def produces_content_types(*content_types):
    # language=rst
    """Decorator for :class:`View <aiohttp.web.View>` request handler methods.

    This method sets ``self.request['best_content_type']`` to one of the
    provided content types.

    Parameters:
        content_types: all content types this handler can produce, best quality
            first.

    Raises:
        web.HTTPNotAcceptable: if none of the available content types are
            acceptable by the client. See :ref:`aiohttp web exceptions
            <aiohttp-web-exceptions>`.

    Example::

        class MyView(aiohttp.web.View):
            @produces_content_types('foo/bar',
                                    'text/baz; charset="utf-8"')
            async def get(self):
                response = aiohttp.web.Response()
                response.content_type = self.request['best_content_type']
                ...
                return response

    """
    if len(content_types) == 1 and not isinstance(content_types[0], str):
        content_types = content_types[0]

    def decorator(f: T.Callable):
        @functools.wraps(f)
        async def wrapper(self, *args, **kwargs):
            request = self.request
            request['best_content_type'] = \
                _best_content_type(request, content_types)
            return await f(self, *args, **kwargs)
        return wrapper

    return decorator
