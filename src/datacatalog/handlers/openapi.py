import copy
import json

from aiohttp import web

from aiohttp_extras.content_negotiation import produces_content_types


_OPENAPI_JSON = None
"""Cache"""


@produces_content_types('application/ld+json', 'application/json')
async def get(request: web.Request):
    # language=rst
    """Produce the OpenAPI3 definition of this service."""
    global _OPENAPI_JSON

    if _OPENAPI_JSON is None:
        openapi_schema = copy.deepcopy(request.app['openapi'])
        c = request.app.config
        # add document schema
        json_schema = await request.app.hooks.mds_json_schema(app=request.app)
        openapi_schema['components']['schemas']['dcat-doc'] = json_schema
        # add base url to servers
        openapi_schema['servers'] = [{'url': c['web']['baseurl']}]
        _OPENAPI_JSON = json.dumps(openapi_schema, indent='  ', sort_keys=True)

    return web.Response(
        text=_OPENAPI_JSON,
        content_type=request['best_content_type']
    )
