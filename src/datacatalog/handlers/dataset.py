import json

from aiohttp import web_exceptions, web


async def get(request: web.Request):
    ...


async def put(request: web.Request):
    hooks = request.app.hooks
    doc = await request.json()
    normalized_doc = await hooks.mds_normalize(doc)
    given_id = request.match_info['dataset']
    for attr in ('dct:identifier', '@id'):
        val = normalized_doc.get(attr, None)
        if val:
            if given_id != val:
                raise web_exceptions.HTTPBadRequest(
                    text='Document identifier mismatch: {} != {}'.format(given_id, val)
                )
            del normalized_doc[attr]
    searchable_text = await hooks.full_text_search_representation(normalized_doc)
    try:
        etag = await hooks.storage_store()
    except ValueError:
        # the given etag doesn't match the stored etag
        ...
    except KeyError:
        raise web_exceptions.HTTPNotFound()
    return web.Response(status=201, headers={'Etag', etag})


async def delete(request: web.Request):
    ...
