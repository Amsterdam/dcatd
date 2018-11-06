import copy
import json

from aiohttp import web

from aiohttp_extras.content_negotiation import produces_content_types


openapi_json = None


@produces_content_types('application/ld+json', 'application/json')
async def get(request: web.Request):
    # language=rst
    """Produce the OpenAPI3 definition of this service."""
    global openapi_json
    if not openapi_json:
        openapi_schema = copy.deepcopy(request.app['openapi'])
        c = request.app.config
        # add document schema
        json_schema = {}
        for method in ['PUT']:
            json_schema[method] = await request.app.hooks.mds_json_schema(
                app=request.app,
                method=method
            )
        # For backward compatibility: the front-end looks at this path:
        openapi_schema['components']['schemas']['dcat-dataset'] = json_schema['PUT']
        # add base url to servers
        openapi_schema['servers'] = [{'url': c['web']['baseurl']}]
        openapi_json = json.dumps(openapi_schema, indent='  ', sort_keys=True)

    return web.Response(
        text=openapi_json,
        content_type=request['best_content_type']
    )


def clear_open_api_cache():
    global openapi_json
    openapi_json = None
