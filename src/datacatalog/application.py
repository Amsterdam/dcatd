import importlib
import urllib.parse
import logging

from aiohttp import web
import aiopluggy

from . import authorization, config, cors, handlers, jwks, openapi, plugin_interfaces

logger = logging.getLogger(__name__)


class Application(web.Application):
    # language=rst
    """The Application.
    """

    def __init__(self, *args, middlewares=None, **kwargs):
        middlewares = [] if middlewares is None else list(middlewares)
        # add required middlewares
        middlewares.extend([
            web.normalize_path_middleware(),  # todo: needed?
            authorization.middleware
        ])
        super().__init__(*args, middlewares=middlewares, **kwargs)

        # Initialize config:
        self._config = config.load()

        self._pool = None

        # set app properties
        path = urllib.parse.urlparse(self._config['web']['baseurl']).path
        if len(path) == 0 or path[-1] != '/':
            path += '/'
        self['path'] = path
        self['openapi'] = openapi.openapi
        self['jwks'] = jwks.load(self._config['jwks'])

        # set routes
        self.router.add_get(path + 'datasets', handlers.datasets.get_collection)
        self.router.add_post(path + 'datasets', handlers.datasets.post_collection)
        self.router.add_route('OPTIONS', path + 'datasets', cors.preflight_handler('POST', 'GET'))

        self.router.add_get(path + 'datasets/{dataset}', handlers.datasets.get)
        self.router.add_put(path + 'datasets/{dataset}', handlers.datasets.put)
        self.router.add_delete(path + 'datasets/{dataset}', handlers.datasets.delete)
        self.router.add_route('OPTIONS', path + 'datasets/{dataset}', cors.preflight_handler('GET', 'DELETE', 'PUT'))

        self.router.add_get(path + 'openapi', handlers.openapi.get)
        self.router.add_route('OPTIONS', path + 'openapi', cors.preflight_handler('GET'))

        self.router.add_get(path + 'system/health', handlers.systemhealth.get)

        # TEMPORARY FIX
        self.router.add_route('OPTIONS', path + 'files', cors.preflight_handler('POST'))

        # Load and initialize plugins:
        self._pm = aiopluggy.PluginManager('datacatalog')
        self._pm.register_specs(plugin_interfaces)

        self.on_startup.append(_on_startup)
        self.on_cleanup.append(_on_cleanup)
        self.on_response_prepare.append(cors.on_response_prepare)

        self._load_plugins()
        self._initialize_sync()
        logger.info("Application initialized")

    def _initialize_sync(self):
        results = self.hooks.initialize_sync(app=self)
        for r in results:
            if r.exception is not None:
                raise r.exception

    @property
    def config(self) -> config.ConfigDict:
        return self._config

    @property
    def pool(self):
        return self._pool

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


async def _on_startup(app):
    results = await app.hooks.initialize(app=app)
    for r in results:
        if r.exception is not None:
            raise r.exception


async def _on_cleanup(app):
    await app.hooks.deinitialize(app=app)


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


