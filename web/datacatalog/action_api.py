from aiohttp import web

from datacatalog import datastore
from datacatalog import search

ACTION_SEARCH = "package_search"
ACTION_SHOW = "package_show"


"""
    Handle the action API calls package_search en package_show
"""
async def handle(request):
    action = request.match_info['action']
    if action == ACTION_SEARCH:
        return await handle_search(request)
    elif action == ACTION_SHOW:
        return await handle_show(request)

    raise web.HTTPNotFound()


async def handle_search(request):
    results = search.search()
    return web.json_response(results)


async def handle_show(request):
    if not 'id' in request.query:
        raise web.HTTPBadRequest()

    id = request.query['id']
    object = datastore.get_by_id(id)
    if not object:
        raise web.HTTPNotFound()

    return web.json_response(object)
