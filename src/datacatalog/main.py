from pkg_resources import resource_stream
import typing as T

from aiohttp import web
import yaml

from datacatalog import application, authorization

_OPENAPI_SCHEMA_RESOURCE = 'openapi.yml'


def main():
    aio_app = application.Application(
        middlewares=[
            _handle_options,
            web.normalize_path_middleware(),
            authorization.middleware
        ])
    with resource_stream(__name__, _OPENAPI_SCHEMA_RESOURCE) as s:
        aio_app['openapi'] = yaml.load(s)
    web.run_app(aio_app, port=aio_app.config['web']['port'])
    return 0


@web.middleware
async def _handle_options(request: web.Request, handler) -> T.Any:
    if request.method == 'OPTIONS':
        return web.Response(
            text='GET,HEAD,OPTIONS,PATCH,POST,PUT',
            status=200,
            headers={
                'Allow': 'GET,HEAD,OPTIONS,PATCH,POST,PUT'
            })
    return await handler(request)


if __name__ == '__main__':
    main()
