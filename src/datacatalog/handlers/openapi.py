from pkg_resources import resource_stream
import typing as T
import json

from aiohttp import web
import yaml

from aiohttp_extras.content_negotiation import produces_content_types


_OPENAPI_SCHEMA_RESOURCE = 'openapi.yml'

_OPENAPI_SCHEMA = None
"""Cache for :func:`_openapi_schema`."""


@produces_content_types('application/ld+json', 'application/json')
async def get(request: web.Request):
    # language=rst
    """Produce the OpenAPI3 definition of this service."""
    openapi_schema = _openapi_schema()
    c = request.app.config
    # add document schema
    primary_schema = c['primarySchema']
    json_schema = await request.app.hooks.mds_json_schema(schema_name=primary_schema)
    openapi_schema['components']['schemas']['dcat-doc'] = json_schema
    # add path to servers
    if 'path' in c['web']:
        openapi_schema['servers'] = [{'url': c['web']['path']}]
    # return the schema
    text = json.dumps(openapi_schema, indent='  ', sort_keys=True)
    return web.Response(
        text=text,
        content_type=request['best_content_type']
    )


def _openapi_schema() -> T.Mapping:
    global _OPENAPI_SCHEMA
    if _OPENAPI_SCHEMA is None:
        with resource_stream(__name__, _OPENAPI_SCHEMA_RESOURCE) as s:
            try:
                _OPENAPI_SCHEMA = yaml.load(s)
            except yaml.YAMLError as e:
                error_msg = "Couldn't load bundled openapi schema '{}'."
                raise Exception(error_msg.format(_OPENAPI_SCHEMA_RESOURCE)) from e
    return _OPENAPI_SCHEMA
