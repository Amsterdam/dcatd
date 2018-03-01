import importlib
import urllib.parse
import logging
from pkg_resources import resource_stream

from aiohttp import hdrs, web
import aiopluggy
import yaml

from . import authorization, config, jwks, plugin_interfaces
from . import handlers

logger = logging.getLogger(__name__)

_OPENAPI_SCHEMA_RESOURCE = 'openapi.yml'


class Application(web.Application):
    # language=rst
    """The Application.
    """

    def __init__(self, *args, **kwargs):
        # add required middlewares
        if 'middlewares' not in kwargs:
            kwargs['middlewares'] = []
        kwargs['middlewares'].extend([
            web.normalize_path_middleware(),  # todo: needed?
            authorization.middleware
        ])
        super().__init__(*args, **kwargs)

        # Initialize config:
        self._config = config.load()

        # set app properties
        path = urllib.parse.urlparse(self._config['web']['baseurl']).path
        if len(path) == 0 or path[-1] != '/':
            path += '/'
        self['path'] = path
        with resource_stream(__name__, _OPENAPI_SCHEMA_RESOURCE) as s:
            self['openapi'] = yaml.load(s)
        self['jwks'] = jwks.load(self._config['jwks'])

        # set routes
        self.router.add_get(path, handlers.index.get)
        self.router.add_get(path + 'datasets', handlers.datasets.get_collection)
        self.router.add_post(path + 'datasets', handlers.datasets.post_collection)
        self.router.add_route('OPTIONS', path + 'datasets', _preflight_handler('POST'))

        self.router.add_get(path + 'datasets/{dataset}', handlers.datasets.get)
        self.router.add_put(path + 'datasets/{dataset}', handlers.datasets.put)
        self.router.add_delete(path + 'datasets/{dataset}', handlers.datasets.delete)
        self.router.add_route('OPTIONS', path + 'datasets/{dataset}', _preflight_handler('PUT', 'DELETE'))

        self.router.add_get(path + 'openapi', handlers.openapi.get)
        self.router.add_get(path + 'system/health', handlers.systemhealth.get)

        # Load and initialize plugins:
        self._pm = aiopluggy.PluginManager('datacatalog')
        self._pm.register_specs(plugin_interfaces)

        self.on_startup.append(self.__class__._on_startup)
        self.on_cleanup.append(self.__class__._on_cleanup)
        self.on_response_prepare.append(_on_response_prepare)

        self._load_plugins()
        self._initialize_sync()

    def _initialize_sync(self):
        results = self.hooks.initialize_sync(app=self)
        for r in results:
            if r.exception is not None:
                raise r.exception

    async def _on_startup(self):
        results = await self.hooks.initialize(app=self)
        for r in results:
            if r.exception is not None:
                raise r.exception

    async def _on_cleanup(self):
        await self.hooks.deinitialize(app=self)

    @property
    def config(self) -> config.ConfigDict:
        return self._config

    @property
    def pm(self) -> aiopluggy.PluginManager:
        return self._pm

    @property
    def hooks(self):
        return self._pm.hooks

    def _load_plugins(self):
        for fq_name in self.config['plugins']:
            plugin = _resolve_plugin_path(fq_name)
            self.pm.register(plugin)
        missing = self.pm.missing()
        if len(missing) > 0:
            raise Exception(
                "There are no implementations for the following required hooks: %s" % missing
            )


def _resolve_plugin_path(fq_name: str):
    """ Resolve the path to a plugin (module, class, or instance).

    :param str fq_name: The fully qualified name of a module, class or instance.
    :raises ModuleNotFoundError: if the module could not be found
    :raises AttributeError: if the plugin could not be found in the module

    """
    segments = fq_name.split('.')
    nseg = len(segments)
    mod = None
    while nseg > 0:
        module_name = '.'.join(segments[:nseg])
        try:
            mod = importlib.import_module(module_name)
            break
        except ModuleNotFoundError:
            pass
        nseg = nseg - 1
    if mod is None:
        raise ModuleNotFoundError(fq_name)
    result = mod
    for segment in segments[nseg:]:
        result = getattr(result, segment)
    return result


###########################################################################
## CORS HANDLING. Everything below this point is copied and adapted from ##
## aiolibs-cors, which does not support aiohttp >= 3.x yet.              ##
###########################################################################


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


async def _on_response_prepare(request: web.Request,
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


def _preflight_handler(*allowed_methods):

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
