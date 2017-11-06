from aiohttp import web

from datacatalog import datastore
from datacatalog import search


async def handle(request):
    """Handle the system health check

    Any failure in the systems that the catalog depends upon should result in a
    status 500. If all systems are go status 200 is returned

    """
    if not await datastore.is_healthy():
        raise web.HTTPServerError(text="datastore not healthy")

    if not await search.is_healthy():
        raise web.HTTPServerError(text="search is not healthy")

    text = "Datacatalog-core systemhealth is OK"
    return web.Response(text=text)
