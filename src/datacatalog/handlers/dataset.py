import urllib.parse
import json.decoder

from aiohttp import web_exceptions, web
from pyld import jsonld

from aiohttp_extras import conditional
from aiohttp_extras.content_negotiation import produces_content_types

_DCAT_ID_KEY = '@id'
_DCAT_DC_ID_KEY = 'http://purl.org/dc/elements/1.1/identifier'


@produces_content_types('application/ld+json', 'application/json')
async def get(request: web.Request):
    docid = request.match_info['dataset']
    etag_if_none_match = conditional.parse_if_header(
        request, conditional.HEADER_IF_MATCH
    )
    if etag_if_none_match == '*':
        raise web_exceptions.HTTPBadRequest(
            body='Endpoint does not support * in the If-None-Match header.'
        )
    # now we know the etag is either None or a set
    try:
        doc, etag = await request.app.hooks.storage_retrieve(
            docid=docid, etags=etag_if_none_match
        )
    except KeyError:
        raise web_exceptions.HTTPNotFound()
    return web.json_response(doc, headers={'Etag': etag})


async def put(request: web.Request):
    hooks = request.app.hooks
    # Grab the document from the request body and canonicalize it.
    try:
        doc = await request.json()
    except json.decoder.JSONDecodeError:
        raise web_exceptions.HTTPBadRequest(text='invalid json')
    cannonical_doc = await hooks.mds_canonicalize(data=doc)

    # Make sure the docid in the path corresponds to the ids given in the
    # document, if any. The assumption is that request.path (which corresponds
    # to the path part of the incoming HTTP request) is the path as seen by
    # the client. This is not necessarily true.
    baseurl = request.app.config['web']['baseurl']
    parsed_baseurl = urllib.parse.urlparse(baseurl)
    root = baseurl[:-len(parsed_baseurl.path)] + '/'
    docurl = urllib.parse.urljoin(root, request.path)
    docid = request.match_info['dataset']
    expanded_doc = jsonld.expand(cannonical_doc)
    if _DCAT_ID_KEY in expanded_doc:
        if expanded_doc[_DCAT_ID_KEY] != docurl:
            raise web_exceptions.HTTPBadRequest(
                text='Invalid {}: {} != {}'.format(
                    _DCAT_ID_KEY, expanded_doc[_DCAT_ID_KEY], docurl
                )
            )
        del expanded_doc[_DCAT_ID_KEY]
    if _DCAT_DC_ID_KEY in expanded_doc:
        if expanded_doc[_DCAT_DC_ID_KEY][0]['@value'] != docid:
            raise web_exceptions.HTTPBadRequest(
                text='Invalid {}: {} != {}'.format(
                    _DCAT_DC_ID_KEY, expanded_doc[_DCAT_DC_ID_KEY], docid
                )
            )
        del expanded_doc[_DCAT_DC_ID_KEY]

    # Let the metadata plugin grab the full-text search representation
    searchable_text = await hooks.mds_full_text_search_representation(
        data=cannonical_doc
    )

    # Figure out the mode (insert / update) of the request.
    etag_if_match = conditional.parse_if_header(
        request, conditional.HEADER_IF_MATCH
    )
    etag_if_none_match = conditional.parse_if_header(
        request, conditional.HEADER_IF_NONE_MATCH
    )
    # Can't accept a value in both headers
    if etag_if_match is not None and etag_if_none_match is not None:
        raise web_exceptions.HTTPBadRequest(
            body='Endpoint supports either If-Match or If-None-Match in a '
                 'single request, not both'
        )

    # If-Match: {etag, ...} is for updates
    if etag_if_match is not None:
        if etag_if_match == '*':
            raise web_exceptions.HTTPBadRequest(
                body='Endpoint does not support If-Match: *. Must provide one '
                     'or more Etags.'
            )
        try:
            new_etag = await hooks.storage_update(
                docid=docid, doc=cannonical_doc, searchable_text=searchable_text,
                etags=etag_if_match, iso_639_1_code="nl"
            )
        except ValueError:
            raise web_exceptions.HTTPPreconditionFailed()
        return web.Response(status=204, headers={'Etag': new_etag})

    # If-None-Match: * is for creates
    if etag_if_none_match != '*':
        raise web_exceptions.HTTPBadRequest(
            body='For inserts of new documents, provide If-None-Match: *'
        )
    try:
        new_etag = await hooks.storage_create(
            docid=docid, doc=cannonical_doc, searchable_text=searchable_text,
            iso_639_1_code="nl"
        )
    except KeyError:
        raise web_exceptions.HTTPPreconditionFailed()
    return web.Response(status=201, headers={'Etag': new_etag})


async def delete(request: web.Request):
    given_id = request.match_info['dataset']
    etag_if_match = conditional.parse_if_header(request, conditional.HEADER_IF_MATCH)
    if etag_if_match is None or etag_if_match == '*':
        raise web_exceptions.HTTPBadRequest(
            text='Must provide a If-Match header containing one or more ETags.'
        )
    try:
        await request.app.hooks.storage_delete(docid=given_id, etags=etag_if_match)
    except KeyError:
        raise web_exceptions.HTTPNotFound()
    return web.Response(status=204)
