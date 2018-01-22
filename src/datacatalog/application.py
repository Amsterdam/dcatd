import importlib

from aiohttp import web
from aiopluggy import PluginManager

from . import config, plugin_interfaces
from .handlers import index, action_api, systemhealth


class Application(web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.router.add_get('/', index.handle)
        self.router.add_get('/system/health', systemhealth.handle)
        self.router.add_get('/datacatalog/api/3/action/{action}', action_api.handle)

        # Initialize config:
        self._config = config.load()

        # Load and initialize plugins:
        self._pm = PluginManager('datacatalog')
        self._pm.register_specs(plugin_interfaces)

        async def on_startup(app):
            await app.hooks.initialize(app=app)
        self.on_startup.append(on_startup)

        async def on_cleanup(app):
            await app.hooks.deinitialize(app=app)
        self.on_cleanup.append(on_cleanup)

        self._load_plugins()
        self.hooks.initialize_sync(app=self)

    @property
    def config(self) -> config.ConfigDict:
        return self._config

    @property
    def pm(self) -> PluginManager:
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

    :param fq_name:
    :raises ModuleNotFoundError: if the module could not be found
    :raises AttributeError: if the plugin could not be found in the module

    """
    segments = fq_name.split('.')
    nseg = len(segments)
    module = None
    while nseg > 0:
        module_name = '.'.join(segments[:nseg])
        try:
            module = importlib.import_module(module_name)
            break
        except ModuleNotFoundError:
            pass
        nseg = nseg - 1
    if module is None:
        raise ModuleNotFoundError(fq_name)
    result = module
    for segment in segments[nseg:]:
        result = getattr(result, segment)
    return result