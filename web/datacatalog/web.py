from aiohttp import web
from datacatalog.app import app

web.run_app(app, port=8000)
