import importlib

from aiohttp import web
import aiopluggy

from . import config, plugin_interfaces
from . import handlers


class Application(web.Application):
    # language=rst
    """The Application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize config:
        self._config = config.load()

        path = ('path' in self._config['web'] and self._config['web']['path']) or ''
        self.router.add_get(path + '/', handlers.index.get)
        self.router.add_get(path + '/datasets', handlers.datasets.get)
        self.router.add_post(path + '/datasets', handlers.datasets.post)
        self.router.add_get(path + '/datasets/{dataset}', handlers.dataset.get)
        self.router.add_put(path + '/datasets/{dataset}', handlers.dataset.put)
        self.router.add_delete(path + '/datasets/{dataset}', handlers.dataset.delete)
        self.router.add_get(path + '/system/health', handlers.systemhealth.get)
        self.router.add_get(path + '/openapi', handlers.openapi.get)

        # Load and initialize plugins:
        self._pm = aiopluggy.PluginManager('datacatalog')
        self._pm.register_specs(plugin_interfaces)

        self.on_startup.append(self.__class__._on_startup)
        self.on_cleanup.append(self.__class__._on_cleanup)

        self._load_plugins()
        self.hooks.initialize_sync(app=self)

    async def _on_startup(self):
        results = await self.hooks.initialize(app=self)
        for r in results:
            if r.exception is not None:
                raise r.exception
        self.assert_primary_schema()

    async def _on_cleanup(self):
        await self.hooks.deinitialize(app=self)

    def assert_primary_schema(self):
        primary_schema = self.config['primarySchema']
        implemented_schemas = [ r.value for r in self.hooks.mds_name() ]
        assert primary_schema in implemented_schemas, \
            "Primary schema '{}' not implemented by any plugin.".format(primary_schema)

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
