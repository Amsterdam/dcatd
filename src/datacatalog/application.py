import importlib
import inspect

from aiohttp import web

from . import config, plugin_specs
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
        self._plugins = self.load()

        self.on_startup.append(_start_plugins)
        self.on_cleanup.append(_stop_plugins)

    @property
    def config(self) -> config.ConfigDict:
        return self._config

    @property
    def plugins(self) -> plugin_specs.Plugins:
        return self._plugins

    def load(self):
        self['loaded_plugins'] = []
        implementations = {}
        for fq_name in self.config['plugins']:
            plugin_class = _load_plugin_class(fq_name)
            _validate_config_for_plugin(self.config, plugin_class, fq_name)

            # Instantiate and register the plugin:
            plugin = plugin_class(self)
            self['loaded_plugins'].append((fq_name, plugin))
            for interface in plugin_specs.implemented_interfaces(plugin):
                implementations[interface] = plugin

        # Assert that all required interfaces are implemented:
        for name in plugin_specs.Plugins._fields:
            if name not in implementations:
                raise Exception(
                    "No plugin configured for '{}' feature.".format(name)
                )

        # Warn about unused plugins:
        for fq_name, plugin in self['loaded_plugins']:
            if not any(
                plugin is i for i in implementations.values()
            ):
                config.logger.warning("Plugin {} unused.".format(fq_name))

        return plugin_specs.Plugins(**implementations)

    async def unload(app):
        global _instances
        for fq_class_name, plugin in reversed(_instances):
            if hasattr(plugin, 'plugin_stop'):
                try:
                    await plugin.plugin_stop()
                except Exception as e:
                    config.logger.warning(
                        "Caught exception while unloading plugin {}".format(fq_class_name),
                        exc_info=e
                    )
                else:
                    config.logger.info("Unloaded plugin {}".format(fq_class_name))
        _instances = []


def _load_plugin_class(fq_class_name):
    segments = fq_class_name.split('.')
    module_name = '.'.join(segments[:-1])
    class_name = segments[-1]
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        raise Exception("Couldn't load module {}".format(module_name)) from e
    try:
        plugin_class = getattr(module, class_name)
    except AttributeError:
        raise Exception(
            "Class {} not found in module {}".format(class_name, module_name)
        ) from None
    if not inspect.isclass(plugin_class):
        raise Exception("Couldn't load plugin: {} is not a class".format(fq_class_name))
    return plugin_class


# noinspection PyPep8Naming
def _validate_config_for_plugin(config, plugin_class, fq_name):
    if hasattr(plugin_class, 'plugin_config_schema'):
        plugin_config_schema = plugin_class.plugin_config_schema
        if callable(plugin_config_schema):
            plugin_config_schema = plugin_config_schema()
        try:
            config.validate(plugin_config_schema)
        except Exception as e:
            raise Exception(
                "Config validation failed for plugin {}".format(fq_name)
            ) from e


async def _start_plugins(app):
    app['started_plugins'] = []
    for fq_name, plugin in app['loaded_plugins']:
        if hasattr(plugin, 'plugin_start'):
            try:
                await plugin.plugin_start(app)
            except Exception as e:
                raise Exception(
                    "Caught exception while initializing plugin {}".format(fq_name)
                ) from e
            else:
                config.logger.info("Initialized plugin {}".format(fq_name))
                app['started_plugins'].append(plugin)


async def _stop_plugins(app):
    for fq_name, plugin in reversed(app['started_plugins']):
        if hasattr(plugin, 'plugin_stop'):
            try:
                await plugin.plugin_stop(app)
            except Exception as e:
                config.logger.warning(
                    "Caught exception while stopping plugin {}".format(fq_name),
                    exc_info=e
                )
            else:
                config.logger.info("Stopped plugin {}".format(fq_name))

