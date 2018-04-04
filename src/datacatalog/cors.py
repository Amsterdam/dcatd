# language=rst
""" CORS handling.

Everything in this file was copied and adapted from aiolibs-cors, which does not
support `aiohttp` >= 3.x yet.

"""

import aiohttp.hdrs as hdrs
import aiohttp.web as web


# Positive response to Access-Control-Allow-Credentials
_TRUE = "true"
# CORS simple response headers:
# <http://www.w3.org/TR/cors/#simple-response-header>
_SIMPLE_RESPONSE_HEADERS = frozenset([
    hdrs.CACHE_CONTROL,
    hdrs.CONTENT_LANGUAGE,
    hdrs.CONTENT_TYPE,
    hdrs.EXPIRES,
    hdrs.LAST_MODIFIED,
    hdrs.PRAGMA
])


async def on_response_prepare(request: web.Request,
                              response: web.StreamResponse):
    """Non-preflight CORS request response processor. Adapted from aiolibs-cors.
    If request is done on CORS-enabled route, process request parameters
    and set appropriate CORS response headers.
    """
    # preflight requests have an own handler
    if request.method == 'OPTIONS':
        return
    # Processing response of non-preflight CORS-enabled request.

    # Handle according to part 6.1 of the CORS specification.

    origin = request.headers.get(hdrs.ORIGIN)
    if origin is None:
        # Terminate CORS according to CORS 6.1.1.
        return

    assert hdrs.ACCESS_CONTROL_ALLOW_ORIGIN not in response.headers
    assert hdrs.ACCESS_CONTROL_ALLOW_CREDENTIALS not in response.headers
    assert hdrs.ACCESS_CONTROL_EXPOSE_HEADERS not in response.headers

    # Process according to CORS 6.1.4.
    # Set exposed headers (server headers exposed to client) before
    # setting any other headers.
    # Expose all headers that are set in response.
    exposed_headers = \
        frozenset(response.headers.keys()) - _SIMPLE_RESPONSE_HEADERS
    response.headers[hdrs.ACCESS_CONTROL_EXPOSE_HEADERS] = \
        ",".join(exposed_headers)

    # Process according to CORS 6.1.3.
    # Set allowed origin.
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = origin
    # Set allowed credentials.
    response.headers[hdrs.ACCESS_CONTROL_ALLOW_CREDENTIALS] = _TRUE


def _parse_request_method(request: web.Request):
    """Parse Access-Control-Request-Method header of the preflight request
    """
    method = request.headers.get(hdrs.ACCESS_CONTROL_REQUEST_METHOD)
    if method is None:
        raise web.HTTPForbidden(
            text="CORS preflight request failed: "
                 "'Access-Control-Request-Method' header is not specified")

    # FIXME: validate method string (ABNF: method = token), if parsing
    # fails, raise HTTPForbidden.

    return method


def _parse_request_headers(request: web.Request):
    """Parse Access-Control-Request-Headers header or the preflight request

    Returns set of headers in upper case.
    """
    headers = request.headers.get(hdrs.ACCESS_CONTROL_REQUEST_HEADERS)
    if headers is None:
        return frozenset()

    # FIXME: validate each header string, if parsing fails, raise
    # HTTPForbidden.
    # FIXME: check, that headers split and stripped correctly (according
    # to ABNF).
    headers = (h.strip(" \t").upper() for h in headers.split(","))
    # pylint: disable=bad-builtin
    return frozenset(filter(None, headers))


def preflight_handler(*allowed_methods):

    allowed_methods = set(m.upper() for m in allowed_methods)
    allowed_methods_str = ','.join(allowed_methods)

    async def handler(request: web.Request):
        """CORS preflight request handler"""

        # Handle according to part 6.2 of the CORS specification.

        origin = request.headers.get(hdrs.ORIGIN)
        if origin is None:
            # Terminate CORS according to CORS 6.2.1.
            raise web.HTTPForbidden(
                text="CORS preflight request failed: "
                     "origin header is not specified in the request")

        # CORS 6.2.3. Doing it out of order is not an error.
        request_method = _parse_request_method(request)
        if request_method not in allowed_methods:
            raise web.HTTPForbidden(
                text="CORS preflight request failed: "
                     "Allowed methods are {}".format(allowed_methods_str))

        # CORS 6.2.4
        request_headers = _parse_request_headers(request)

        response = web.Response()

        # CORS 6.2.7
        response.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = origin
        # Set allowed credentials.
        response.headers[hdrs.ACCESS_CONTROL_ALLOW_CREDENTIALS] = _TRUE

        # CORS 6.2.9
        response.headers[hdrs.ACCESS_CONTROL_ALLOW_METHODS] = allowed_methods_str

        # CORS 6.2.10
        if request_headers:
            # Note: case of the headers in the request is changed, but this
            # shouldn't be a problem, since the headers should be compared in
            # the case-insensitive way.
            response.headers[hdrs.ACCESS_CONTROL_ALLOW_HEADERS] = \
                ",".join(request_headers)

        return response
    return handler
