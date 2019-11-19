# language=rst
"""
Module that loads the configuration settings for all our services.

..  envvar:: CONFIG_PATH

    If set, the configuration is loaded from this path.

Example usage::

    from . import config
    CONFIG = config.load()
    os.chdir(CONFIG['working_directory'])


..  py:data:: DEFAULT_CONFIG_PATHS

    :vartype: list[`pathlib.Path`]

    By default, this variable is initialized with:

        -   :file:`/etc/dcatd.yml`
        -   :file:`./config.yml`

"""

# stdlib imports:
import logging
import logging.config
import os
import os.path
import pathlib
import string
import typing as T
from collections import ChainMap

# external dependencies:
import jsonschema
import yaml
from pkg_resources import resource_stream

logger = logging.getLogger(__name__)

_settings = {}
_CONFIG_SCHEMA_RESOURCE = 'config_schema.yml'


DEFAULT_CONFIG_PATHS = [
    pathlib.Path('/etc') / 'dcatd.yml',
    pathlib.Path('config.yml')
]
"""List of locations to look for a configuration file."""


def init_settings():
    global _settings
    _settings = load()


def get_settings():
    global _settings
    if not _settings:
        init_settings()
    return _settings


class ConfigDict(dict):
    def validate(self, schema: T.Mapping):
        # language=rst
        """
        Validate this config dict using the JSON schema given in ``schema``.

        Raises:
            ConfigError: if schema validation failed

        """
        try:
            jsonschema.validate(self, schema)
        except jsonschema.exceptions.SchemaError as e:
            raise ConfigError("Invalid JSON schema definition.") from e
        except jsonschema.exceptions.ValidationError as e:
            raise ConfigError("Schema validation failed.") from e


class ConfigError(Exception):
    # language=rst
    """Configuration Error

    .. todo:: Documentation: When is this error raised?

    """


def _config_schema() -> T.Mapping:
    with resource_stream(__name__, _CONFIG_SCHEMA_RESOURCE) as s:
        try:
            return yaml.load(s, Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            error_msg = "Couldn't load bundled config_schema '{}'."
            raise ConfigError(error_msg.format(_CONFIG_SCHEMA_RESOURCE)) from e


def _load_yaml(path: pathlib.Path) -> dict:
    # language=rst
    """Read the config file from ``path``.

    Raises:
        yaml.YAMLError: syntax error in YAML.
        KeyError: Required environment value not found.

    """
    with path.open() as f:
        try:
            result = yaml.load(f, Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            error_msg = "Couldn't load yaml file '{}'.".format(path)
            raise ConfigError(error_msg.format(path)) from e
        try:
            return _interpolate(result)
        except KeyError as e:
            error_msg = "Missing required environment variable while loading file '{}'."
            raise ConfigError(error_msg.format(path)) from e
        except Exception as e:
            raise ConfigError() from e


def _interpolate(config: dict) -> dict:
    # language=rst
    """Substitute environment variables.

    Recursively find string-type values in the given ``config``,
    and try to substitute them with values from :data:`os.environ`.

    Note:
        If a substituted value is a string containing only digits (i.e.
        :py:meth:`str.isdigit()` is True), then this function will cast
        it to an integer.  It does not try to do any other type conversion.

    :param config: configuration mapping

    """

    def interpolate(value):
        try:
            result = _TemplateWithDefaults(value).substitute(os.environ)
        except KeyError as e:
            error_msg = "Could not substitute: {}"
            raise ConfigError(error_msg.format(value)) from e
        except ValueError as e:
            error_msg = "Invalid substitution: {}"
            raise ConfigError(error_msg.format(value)) from e
        return (result.isdigit() and int(result)) or result

    def interpolate_recursively(obj: T.Union[T.Dict, T.List, str]):
        if isinstance(obj, str):
            return interpolate(obj)
        if isinstance(obj, dict):
            return {key: interpolate_recursively(obj[key]) for key in obj}
        if isinstance(obj, list):
            return [interpolate_recursively(val) for val in obj]
        return obj

    return {key: interpolate_recursively(config[key]) for key in config}


class _TemplateWithDefaults(string.Template):
    # language=rst
    """
    String template that supports Bash-style default values for interpolation.

    Copied from `Docker Compose
    <https://github.com/docker/compose/blob/master/compose/config/interpolation.py>`_

    """
    # string.Template uses cls.idpattern to define identifiers:
    idpattern = r'[_a-z][_a-z0-9]*(?::?-[^}]+)?'

    # Modified from python2.7/string.py
    def substitute(*args, **kws):
        if not args:
            raise TypeError("descriptor 'substitute' of 'Template' object "
                            "needs an argument")
        self, *args = args  # allow the "self" keyword be passed
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = ChainMap(kws, args[0])
        else:
            mapping = args[0]

        # Helper function for .sub()
        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                if ':-' in named:
                    var, _, default = named.partition(':-')
                    return mapping.get(var) or default
                if '-' in named:
                    var, _, default = named.partition('-')
                    return mapping.get(var, default)
                val = mapping.get(named, "")
                return '%s' % (val,)
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)


def _config_path() -> pathlib.Path:
    # language=rst
    """Determines which path to use for the configuration file.

    Raises:
        FileNotFoundError: if no config file could be found at any location.

    """
    config_paths = [pathlib.Path(os.getenv('CONFIG_PATH'))] \
        if os.getenv('CONFIG_PATH') \
        else DEFAULT_CONFIG_PATHS

    filtered_config_paths = list(filter(
        lambda path: path.exists() and path.is_file(),
        config_paths
    ))

    if 0 == len(filtered_config_paths):
        error_msg = 'No configfile found at {}'
        paths_as_string = ' or '.join(str(p) for p in config_paths)
        raise FileNotFoundError(error_msg.format(paths_as_string))
    return filtered_config_paths[0]


def load() -> ConfigDict:
    # language=rst
    """ Load and validate the configuration.
    """
    config_path = _config_path()
    config = ConfigDict(_load_yaml(config_path))
    if 'logging' not in config:
        raise ConfigError(
            "No 'logging' entry in config file {}".format(config_path)
        )
    logging.config.dictConfig(config['logging'])
    logger.info("Loaded configuration from '%s'", os.path.abspath(str(config_path)))
    config.validate(_config_schema())
    return config
