from aiohttp import web

from datacatalog import app

aio_app = app.get_app()
web.run_app(aio_app, port=aio_app['config']['web']['port'])
