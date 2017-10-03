import logging
from enum import Enum

from aiohttp import web

from datacatalog import datastore
from datacatalog import search

ACTION_PARAM = 'action'
ACTION_SHOW = "package_show"
ACTION_LIST = "package_list"
ACTION_SEARCH = "package_search"


class SearchParams(Enum):
    START = "start"
    ROWS = "rows"
    FACET_FIELD = "facet.field"
    FACET_QUERY = "fq"
    SORT = "sort"

log = logging.getLogger(__name__)


"""
    Handle the action API calls package_search en package_show
"""
async def handle(request):
    action = request.match_info[ACTION_PARAM]
    if action == ACTION_SEARCH:
        return await handle_search(request)
    elif action == ACTION_SHOW:
        return await handle_show(request)
    elif action == ACTION_LIST:
        return await handle_list(request)

    raise web.HTTPNotFound()


def extract_queryparams(request):
    query = {}

    if SearchParams.START.value in request.query:
        query[SearchParams.START] = int(request.query[SearchParams.START.value])
        if query[SearchParams.START] < 0:
            raise ValueError()

    if SearchParams.ROWS.value in request.query:
        query[SearchParams.ROWS] = int(request.query[SearchParams.ROWS.value])
        if query[SearchParams.ROWS] < 1:
            raise ValueError()

    return query



async def handle_search(request):
    try:
        query = extract_queryparams(request)
    except ValueError:
        raise web.HTTPBadRequest()

    results = search.search(query)
    return web.json_response(results)


async def handle_show(request):
    if not 'id' in request.query:
        raise web.HTTPBadRequest()

    id = request.query['id']
    object = datastore.get_by_id(id)
    if not object:
        raise web.HTTPNotFound()

    return web.json_response(object)


async def handle_list(request):
    results = datastore.get_list()
    return web.json_response(results)
