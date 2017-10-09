import json
import logging
from enum import Enum

from aiohttp import web

from datacatalog import datastore
from datacatalog import search

ACTION_PARAM = 'action'
ACTION_SHOW = "package_show"
ACTION_LIST = "package_list"
ACTION_SEARCH = "package_search"


class SearchParam(Enum):
    START = "start"
    ROWS = "rows"
    FACET_FIELDS = "facet.field"
    FACET_QUERY = "fq"
    SORT = "sort"
    # to implement
    QUERY = "q"


class Facet(Enum):
    GROUP = "groups"
    RESOURCE = "res_format"
    PUBLISHER = "organization"

log = logging.getLogger(__name__)


async def handle(request):
    """
        Handle the action API calls package_search en package_show
    """
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

    if SearchParam.START.value in request.query:
        query[SearchParam.START] = int(request.query[SearchParam.START.value])
        if query[SearchParam.START] < 0:
            raise ValueError()

    if SearchParam.ROWS.value in request.query:
        query[SearchParam.ROWS] = int(request.query[SearchParam.ROWS.value])
        if query[SearchParam.ROWS] < 1:
            raise ValueError()

    if SearchParam.FACET_FIELDS.value in request.query:
        data = json.loads(request.query[SearchParam.FACET_FIELDS.value])
        query[SearchParam.FACET_FIELDS] = data

    if SearchParam.FACET_QUERY.value in request.query:
        facets = str(request.query[SearchParam.FACET_QUERY.value]).split()
        keys = [facet.split(':')[0] for facet in facets]
        values = [facet.split(':')[1].strip('"') for facet in facets]
        query[SearchParam.FACET_QUERY] = {k: v for (k, v) in zip(keys, values)}

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
