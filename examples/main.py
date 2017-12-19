from aiohttp import web

from datacatalog import app


def main() -> int:
    aio_app = app.get_app()
    web.run_app(aio_app, port=aio_app['config']['web']['port'])
    return 0


if __name__ == '__main__':
    main()
