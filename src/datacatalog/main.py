import asyncio

from aiohttp import web
import uvloop

from datacatalog import application


def main():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    aio_app = application.Application()
    web.run_app(aio_app, port=aio_app.config['web']['port'])
    return 0


if __name__ == '__main__':
    main()
