from aiohttp import web

from datacatalog import systemhealth, index, action_api, config
from datacatalog.search import Search
from datacatalog.datastore import DataStore


def get_app():
    """
        Construct the the application
    """
    app = web.Application()

    app.router.add_get('/', index.handle)
    app.router.add_get('/system/health', systemhealth.handle)
    app.router.add_get('/datacatalog/api/3/action/{action}', action_api.handle)

    catalog_config = config.load()
    app['config'] = catalog_config

    # Initialize plugins
    app['datastore'] = DataStore(catalog_config).implementation
    app['search'] = Search(catalog_config).implementation

    return app
