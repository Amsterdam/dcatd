import pkg_resources
# import typing as T
import yaml
import logging

from aiohttp import web
import aiohttp

import aiopluggy

_hookimpl = aiopluggy.HookimplMarker('datacatalog')
_logger = logging.getLogger(__name__)

_BASE_URL = None
_AUTHZ_TOKEN = None


@_hookimpl
def initialize_sync(app):
    # language=rst
    """ Initialize the plugin.

    This function validates the configuration and creates a connection pool.
    The pool is stored as a module-scoped singleton in _pool.

    """

    # validate configuration
    with pkg_resources.resource_stream(__name__, 'swift_config_schema.yml') as s:
        schema = yaml.load(s)
    app.config.validate(schema)
    global _BASE_URL, _AUTHZ_TOKEN
    config = app.config['storage_swift']
    _BASE_URL = config['base_url'] + config['project_id'] + '/' + config['container'] + '/'
    _AUTHZ_TOKEN = config['authz_token']


@_hookimpl
async def object_store_writer(name: str, content_type: str, stream: aiohttp.StreamReader):
    response = await aiohttp.request(
        'PUT',
        _BASE_URL + name,
        headers={
            'X-Auth-Token': _AUTHZ_TOKEN,
            'Content-Type': content_type
        },
        chunked=True,
        expect100=True,
        data=stream
    )
    if response.status >= 400:
        _logger.error(
            "Couldn't store file in object store.\n"
            "%s %s:\n%s", response.status, response.reason,
            await response.text()
        )
        raise web.HTTPBadGateway()
