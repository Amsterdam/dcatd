import pkg_resources
import yaml
import logging
import typing as T
from uuid import uuid4

from aiohttp import helpers, web
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

    -  validates the configuration loaded by `app`;
    -  initializes `_BASE_URL` and `_AUTHORIZATION`;
    -  registers a new endpoint ``/files`` in the HTTP service.

    """
    # validate configuration
    with pkg_resources.resource_stream(__name__, 'config_schema.yml') as s:
        schema = yaml.load(s, Loader=yaml.SafeLoader)
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


async def post(request: web.Request) -> web.Response:
    # language=rst
    """POST handler for ``/files``"""
    mimetype = helpers.parse_mimetype(request.headers[aiohttp.hdrs.CONTENT_TYPE])
    if mimetype.type != 'multipart':
        raise web.HTTPBadRequest(
            text='multipart/* content type expected'
        )
    reader = await request.multipart()
    field = await reader.next()
    if field.name != 'distribution':
        raise web.HTTPBadRequest(
            text='file field must be named “distribution”'
        )
    uuid = uuid4().hex
    content_type = field.headers.get(
        aiohttp.hdrs.CONTENT_TYPE,
        'application/octet-stream'
    )
    await _put_file_to_object_store(
        uuid, content_type,
        field, filename=field.filename
    )
    return web.Response(
        status=201,
        headers={
            'Location': _BASE_URL + uuid
        }
    )
