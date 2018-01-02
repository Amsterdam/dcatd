from aiohttp import web


async def handle(request):
    # language=rst
    """Handle the system health check.

    Any failure in the systems that the catalog depends upon should result in a
    status 503 (ie. `aiohttp.web.HTTPServiceUnavailable`). If all systems are go
    status 200 is returned

    """
    datastore = request.app.plugins.datastore
    if not await datastore.datastore_is_healthy():
        raise web.HTTPServiceUnavailable(text="datastore not healthy")

    search = request.app.plugins.search
    if not await search.search_is_healthy():
        raise web.HTTPServiceUnavailable(text="search is not healthy")

    text = "Datacatalog-core systemhealth is OK"
    return web.Response(text=text)
