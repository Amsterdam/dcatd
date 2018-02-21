from aiohttp import web_exceptions, web

from aiohttp_extras import conditional


async def get(request: web.Request):
    given_id = request.match_info['dataset']
    etag_if_none_match = conditional.parse_if_header(request, conditional.HEADER_IF_MATCH)
    if etag_if_none_match == '*':
        raise web_exceptions.HTTPBadRequest(
            body='Endpoint does not support * in the If-None-Match header.'
        )
    # now we know the etag is either None or a set



async def put(request: web.Request):
    hooks = request.app.hooks
    # Grab the document from the request body and normalize it.
    doc = await request.json()
    normalized_doc = await hooks.mds_normalize(doc)
    # Make sure the docid in the path corresponds to the ids given in the
    # document, if any.
    given_id = request.match_info['dataset']
    for attr in ('dct:identifier', '@id'):
        val = normalized_doc.get(attr, None)
        if val:
            if given_id != val:
                raise web_exceptions.HTTPBadRequest(
                    text='Document identifier mismatch: {} != {}'.format(given_id, val)
                )
            del normalized_doc[attr]
    # Let the metadata plugin grab the full-text search representation
    searchable_text = await hooks.mds_full_text_search_representation(normalized_doc)
    # Figure out the mode we're using for the insert.
    etag_if_match = conditional.parse_if_header(request, conditional.HEADER_IF_MATCH)
    etag_if_none_match = conditional.parse_if_header(request, conditional.HEADER_IF_MATCH)
    # Can't accept a value in both headers
    if etag_if_match and etag_if_none_match:
        raise web_exceptions.HTTPBadRequest(
            body='Endpoint supports either If-Match or If-None-Match in a '
                 'single request, not both'
        )

    # If-Match: {etag, ...} is for updates
    if etag_if_match:
        if etag_if_match == '*':
            raise web_exceptions.HTTPBadRequest(
                body='Endpoint does not support If-Match: *. Must provide one '
                     'or more Etags.'
            )
        try:
            new_etag = await hooks.storage_update(
                given_id, normalized_doc, searchable_text, "nl", etag_if_match
            )
        except ValueError:
            raise web_exceptions.HTTPPreconditionFailed()
        except KeyError:
            raise web_exceptions.HTTPNotFound()
        return web.Response(status=204, headers={'Etag', new_etag})

    # If-None-Match: * is for creates
    if etag_if_none_match != '*':
        raise web_exceptions.HTTPBadRequest(
            body='Endpoint does not support specific Etags in the '
                 'If-None-Match header. For inserts of new documents, '
                 'value must be *.'
        )
    try:
        new_etag = await hooks.storage_create(
            given_id, normalized_doc, searchable_text, "nl"
        )
    except KeyError:
        raise web_exceptions.HTTPPreconditionFailed()
    return web.Response(status=201, headers={'Etag', new_etag})


async def delete(request: web.Request):
    ...
