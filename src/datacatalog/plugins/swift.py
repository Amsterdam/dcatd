import pkg_resources
# import typing as T
import yaml
import logging
import re
import typing as T
from uuid import uuid4

from aiohttp import helpers, multipart, web
import aiohttp

import aiopluggy

_hookimpl = aiopluggy.HookimplMarker('datacatalog')
_logger = logging.getLogger(__name__)

_BASE_URL = None
_AUTHORIZATION = None


@_hookimpl
def initialize_sync(app):
    # language=rst
    """ Initialize the plugin.

    This function validates the configuration and creates a connection pool.
    The pool is stored as a module-scoped singleton in _pool.

    :param datacatalog.application.Application app:

    """
    # validate configuration
    with pkg_resources.resource_stream(__name__, 'swift_config_schema.yml') as s:
        schema = yaml.load(s)
    app.config.validate(schema)
    global _BASE_URL, _AUTHORIZATION
    config = app.config['storage_swift']
    _BASE_URL = config['base_url'] + config['container'] + '/'
    _AUTHORIZATION = aiohttp.BasicAuth(config['user'], config['password']).encode()
    app.router.add_post(app['path'] + 'files', post)


async def _put_file_to_object_store(uuid: str, content_type: str, data,
                                    filename: T.Optional[str]=None):
    _logger.debug("url: %s\n", _BASE_URL + uuid)
    _logger.debug("Authorization: %s", _AUTHORIZATION)
    headers = {
        'Authorization': _AUTHORIZATION,
        'Content-Type': content_type
    }
    if filename is not None:
        headers['Content-Disposition'] = helpers.content_disposition_header(
            'attachment', filename=filename
        )
    async with aiohttp.ClientSession() as session:
        async with session.put(
            _BASE_URL + uuid,
            data=data,
            headers=headers,
            chunked=True,
            expect100=True
        ) as response:
            if response.status >= 400:
                _logger.error(
                    "Couldn't store file in object store.\n"
                    "%s %s:\n%s\n%r", response.status, response.reason,
                    await response.text(), response
                )
                raise web.HTTPBadGateway()


@aiohttp.streamer
async def _streamer(sink, source):
    while True:
        chunk = await source.read_chunk(size=65536)
        if not chunk:
            break
        await sink.write(chunk)


async def post(request: web.Request) -> web.Response:
    # language=rst
    """POST handler for ``/files``"""
    reader = await request.multipart()
    field = await reader.next()
    assert field.name == 'distribution'
    filename = field.filename
    uuid = uuid4().hex
    await _put_file_to_object_store(
        uuid, request.content_type,
        field, filename=filename
    )
    return web.Response(
        status=201,
        headers={
            'Location': _BASE_URL + uuid
        }
    )
