from aiohttp import web

from datacatalog import application


def main():
    aio_app = application.Application(middlewares=[_handle_options])
    web.run_app(aio_app, port=aio_app.config['web']['port'])
    return 0


@web.middleware
async def _handle_options(request: web.Request, handler):
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
