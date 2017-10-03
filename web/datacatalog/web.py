from aiohttp import web

from datacatalog import app

web.run_app(app.get_app(), port=8000)
