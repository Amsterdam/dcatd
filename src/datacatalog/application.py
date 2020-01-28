import importlib
import urllib.parse
import logging

from aiohttp import web
import aiohttp_cors
import aiopluggy

from datacatalog import startup_actions
from datacatalog.handlers.openapi import clear_open_api_cache
from datacatalog.plugins.postgres import listen_notifications

from . import authorization, config, handlers, openapi, plugin_interfaces

logger = logging.getLogger(__name__)


class Application(web.Application):
    # language=rst
    """ The Application.

    .. todo::

        Inheritance from ``web.Application`` is discouraged by aiohttp. This
        class, with its initializer, must be replaced by an application factory
        method that builds an application object from ``web.Application``.

    """

    def __init__(self, *args, middlewares=None, **kwargs):
        middlewares = [] if middlewares is None else list(middlewares)
        # add required middlewares
        middlewares.extend([
            web.normalize_path_middleware(),  # todo: needed?
            # Make comment from the following line to disable authentication for local testing
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

        # set routes
        self.router.add_get(path + 'datasets', handlers.datasets.get_collection)
        self.router.add_post(path + 'datasets', handlers.datasets.post_collection)

        self.router.add_get(path + 'datasets/{dataset}', handlers.datasets.get)
        self.router.add_put(path + 'datasets/{dataset}', handlers.datasets.put)
        self.router.add_delete(path + 'datasets/{dataset}', handlers.datasets.delete)
        self.router.add_get(path + 'datasets/{dataset}/purls/{distribution}', handlers.datasets.link_redirect)

        self.router.add_get(path + 'harvest', handlers.harvest.get_collection)

        self.router.add_get(path + 'openapi', handlers.openapi.get)

        self.router.add_get(path + 'system/health', handlers.systemhealth.get)

        # Load and initialize plugins:
        self._pm = aiopluggy.PluginManager('datacatalog')
        self._pm.register_specs(plugin_interfaces)

        self.on_startup.append(_on_startup)
        self.on_cleanup.append(_on_cleanup)

        self._load_plugins()
        self._initialize_sync()

        # CORS
        # this must be done after initialize_sync: plugins may register new
        # routes during setup and our allow_cors applies to all routes.
        if 'allow_cors' in self._config['web'] and self._config['web']['allow_cors']:
            cors = aiohttp_cors.setup(self, defaults={
                '*': aiohttp_cors.ResourceOptions(
                    expose_headers="*", allow_headers="*"
                ),
            })
            for route in list(self.router.routes()):
                cors.add(route)

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

    @staticmethod
    def notify_callback(conn, pid, channel, payload):
        if channel == 'channel' and payload == 'data_changed':
            clear_open_api_cache()


async def _on_startup(app):
    results = await app.hooks.initialize(app=app)
    for r in results:
        if r.exception is not None:
            raise r.exception
    await startup_actions.run_startup_actions(app)

    # listen to Postgres notifications
    await listen_notifications(app, app.notify_callback)


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
