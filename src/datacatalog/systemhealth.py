from aiohttp import web


async def handle(request):
    """Handle the system health check

    Any failure in the systems that the catalog depends upon should result in a
    status 500. If all systems are go status 200 is returned

    """
    datastore = request.app['datastore']
    if not await datastore.is_healthy():
        raise web.HTTPServiceUnavailable(text="datastore not healthy")

    search = request.app['search']
    if not await search.is_healthy():
        raise web.HTTPServiceUnavailable(text="search is not healthy")

    text = "Datacatalog-core systemhealth is OK"
    return web.Response(text=text)
