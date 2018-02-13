import importlib

from aiohttp import web
import aiopluggy

from . import config, plugin_interfaces
from .handlers import index, systemhealth


class Application(web.Application):
    # language=rst
    """The Application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.router.add_get('/', index.handle)
        self.router.add_get('/system/health', systemhealth.handle)

        # Initialize config:
        self._config = config.load()

        # Load and initialize plugins:
        self._pm = aiopluggy.PluginManager('datacatalog')
        self._pm.register_specs(plugin_interfaces)

        async def on_startup(app):
            results = await app.hooks.initialize(app=app)
            for r in results:
                if r.exception is not None:
                    raise r.exception
            self.assert_primary_schema()
            print(await self.hooks.mds_json_schema(schema_name='dcat-ap-ams'))
        self.on_startup.append(on_startup)

        async def on_cleanup(app):
            await app.hooks.deinitialize(app=app)
        self.on_cleanup.append(on_cleanup)

        self._load_plugins()
        self.hooks.initialize_sync(app=self)

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
