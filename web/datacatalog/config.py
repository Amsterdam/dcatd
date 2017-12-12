# language=rst
"""
Module that loads the configuration settings for all our services.

..  envvar:: CONFIG_PATH

    If set, the configuration is loaded from this path.

See also :mod:`config_loader`.

Example usage::

    from authz_admin import config
    os.chdir(config.get()['working_directory'])


..  py:data:: CONFIG_SCHEMA_V1_PATH

    :vartype: `pathlib.Path`

..  py:data:: DEFAULT_CONFIG_PATHS

    :vartype: list[`pathlib.Path`]

    By default, this variable is initialized with:

        -   :file:`/etc/datacatalog.yml`
        -   :file:`./datacatalog.yml`

"""

# stdlib imports:
import logging
import logging.config
import os.path
import pathlib
import types

# extra imports:
import config_loader

_logger = logging.getLogger(__name__)


DEFAULT_CONFIG_PATHS = [
    pathlib.Path('/etc') / 'datacatalog.yml',
    pathlib.Path('config.yml')
]


CONFIG_SCHEMA_PATH = pathlib.Path(
    os.path.dirname(os.path.abspath(__file__))
) / 'config_schema.yml'


def _config_path() -> pathlib.Path:
    # language=rst
    """
    Determines which path to use for the configuration file.

    :rtype: pathlib.Path
    :raises: FileNotFoundError

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


def load() -> types.MappingProxyType:
    # language=rst
    """
    Load and validate the configuration.

    :rtype: types.MappingProxyType

    .. todo:: Log the chosen path with proper log level.

    """
    config_path = _config_path()
    config = config_loader.load(
        config_path,
        CONFIG_SCHEMA_PATH
    )
    logging.config.dictConfig(config['logging'])
    _logger.info("Loaded configuration from '%s'", os.path.abspath(config_path))

    # Procedure logging.config.dictConfig() (called above) requires a
    # MutableMapping as its input, so we only freeze config *after* that call:
    config = config_loader.freeze(config)
    return config
