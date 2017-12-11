from aiohttp import web

from . import systemhealth, index, action_api, config


def get_app():
    """
        Construct the the application
    """
    app = web.Application()

    app.router.add_get('/', index.handle)
    app.router.add_get('/system/health', systemhealth.handle)

    app.router.add_get('/datacatalog/api/3/action/{action}', action_api.handle)

    app['config'] = config.load()

    return app
