import csv
import json.decoder
import logging
import re
import typing as T

from aiohttp import web

from aiohttp_extras import conditional
from aiohttp_extras.content_negotiation import produces_content_types


_logger = logging.getLogger(__name__)

_FACET_QUERY_KEY = re.compile(
    r'(?:/properties/[^/=~<>]+(?:/items)?)+'
)
_FACET_QUERY_VALUE = re.compile(
    r'(in|eq|gt|lt|ge|le)=(.*)', flags=re.S
)


@produces_content_types('application/ld+json', 'application/json')
async def get(request: web.Request):
    hooks = request.app.hooks
    docid = request.match_info['dataset']
    etag_if_none_match = conditional.parse_if_header(
        request, conditional.HEADER_IF_NONE_MATCH
    )
    if etag_if_none_match == '*':
        raise web.HTTPBadRequest(
            body='Endpoint does not support * in the If-None-Match header.'
        )
    # Now we know etag_if_none_match is either None or a set.
    try:
        doc, etag = await hooks.storage_retrieve(
            app=request.app, docid=docid, etags=etag_if_none_match
        )
    except KeyError:
        raise web.HTTPNotFound()
    if doc is None:
        return web.Response(status=304, headers={'Etag': etag})
    canonical_doc = await hooks.mds_canonicalize(app=request.app, data=doc)
    canonical_doc = await hooks.mds_after_storage(app=request.app, data=canonical_doc, doc_id=docid)

    return web.json_response(canonical_doc, headers={
        'Etag': etag, 'content_type': 'application/ld+json'
    })


async def put(request: web.Request):
    hooks = request.app.hooks

    if hasattr(request, "authz_subject"):
        subject = request.authz_subject
        scopes = request.authz_scopes
        _logger.warning(f"AUTHZ  subject {subject}, scopes {scopes}")
    # Grab the document from the request body and canonicalize it.
    try:
        doc = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest(text='invalid json')
    canonical_doc = await hooks.mds_canonicalize(app=request.app, data=doc)

    # Make sure the docid in the path corresponds to the ids given in the
    # document, if any. The assumption is that request.path (which corresponds
    # to the path part of the incoming HTTP request) is the path as seen by
    # the client. This is not necessarily true.
    doc_id = request.match_info['dataset']

    # Let the metadata plugin grab the full-text search representation
    searchable_text = await hooks.mds_full_text_search_representation(
        data=canonical_doc
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
        raise web.HTTPBadRequest(
            body='Endpoint supports either If-Match or If-None-Match in a '
                 'single request, not both'
        )

    # If-Match: {etag, ...} is for updates
    if etag_if_match is not None:
        if etag_if_match == '*':
            raise web.HTTPBadRequest(
                body='Endpoint does not support If-Match: *. Must provide one '
                     'or more Etags.'
            )
        try:
            old_doc, _etag = await hooks.storage_retrieve(
                app=request.app, docid=doc_id, etags=None
            )
        except KeyError:
            raise web.HTTPPreconditionFailed()
        canonical_doc = await hooks.mds_before_storage(
            app=request.app, data=canonical_doc, old_data=old_doc
        )
        try:
            new_etag = await hooks.storage_update(
                app=request.app, docid=doc_id, doc=canonical_doc,
                searchable_text=searchable_text, etags=etag_if_match,
                iso_639_1_code="nl"
            )
        except ValueError:
            raise web.HTTPPreconditionFailed()
        retval = web.Response(status=204, headers={'Etag': new_etag})

    else:
        # If-None-Match: * is for creates
        if etag_if_none_match != '*':
            raise web.HTTPBadRequest(
                body='For inserts of new documents, provide If-None-Match: *'
            )
        canonical_doc = await hooks.mds_before_storage(
            app=request.app, data=canonical_doc
        )
        try:
            new_etag = await hooks.storage_create(
                app=request.app, docid=doc_id, doc=canonical_doc,
                searchable_text=searchable_text, iso_639_1_code="nl"
            )
        except KeyError:
            raise web.HTTPPreconditionFailed()
        retval = web.Response(
            status=201, headers={'Etag': new_etag}, content_type='text/plain'
        )

    return retval


async def delete(request: web.Request):
    given_id = request.match_info['dataset']
    etag_if_match = conditional.parse_if_header(request, conditional.HEADER_IF_MATCH)
    if etag_if_match is None or etag_if_match == '*':
        raise web.HTTPBadRequest(
            text='Must provide a If-Match header containing one or more ETags.'
        )
    try:
        await request.app.hooks.storage_delete(
            app=request.app, docid=given_id, etags=etag_if_match)
    except KeyError:
        raise web.HTTPNotFound()
    return web.Response(status=204, content_type='text/plain')


@produces_content_types('application/ld+json', 'application/json')
async def get_collection(request: web.Request) -> web.StreamResponse:
    # language=rst
    """Handler for ``/datasets``"""
    hooks = request.app.hooks
    query = request.query
    scopes = request.authz_scopes if hasattr(request, "authz_scopes") else {}

    # show non-available datasets only to admin or redactor
    if 'CAT/R' in scopes or 'CAT/W' in scopes:
        filters = {}
    else:
        filters = {
            '/properties/ams:status': {
                'eq': 'beschikbaar'
            }
        }

    # Extract facet filters:
    for key in query:
        if not _FACET_QUERY_KEY.fullmatch(key) or (not admin and key == '/properties/ams:status'):
            continue
        if key not in filters:
            filters[key] = {}
        match: T.List[str] = _FACET_QUERY_VALUE.fullmatch(query[key])
        if not match:
            raise web.HTTPBadRequest(
                text="Unknown comparator in query parameter '%s'" % key
            )
        comparator = match[1]
        value = match[2]
        if comparator in filters[key]:
            raise web.HTTPBadRequest(
                text="Multiple facet filters for facet %s with comparator %s" %
                     (key, comparator)
            )
        if comparator == 'in':
            value = _csv_decode_line(value)
            if value is None:
                raise web.HTTPBadRequest(
                    text="Value of query parameter '%s' is not a CSV encoded list of strings; see RFC4180" % key
                )
        filters[key][comparator] = value

    full_text_query = query.get('q', '').strip()
    limit = query.get('limit', None)
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            raise web.HTTPBadRequest(
                text="Invalid limit value %s" % limit
            )
    offset = query.get('offset', 0)
    if offset is not None:
        try:
            offset = int(offset)
        except ValueError:
            raise web.HTTPBadRequest(
                text="Invalid offset value %s" % offset
            )

    result_info = {}
    facets = [
                 '/properties/dcat:distribution/items/properties/ams:resourceType',
                 '/properties/dcat:distribution/items/properties/dcat:mediaType',
                 '/properties/dcat:distribution/items/properties/dct:format',
                 '/properties/dcat:distribution/items/properties/ams:distributionType',
                 '/properties/dcat:distribution/items/properties/ams:serviceType',
                 '/properties/dcat:keyword/items',
                 '/properties/dcat:theme/items',
                 '/properties/ams:owner'
             ]
    if admin:
        facets.append('/properties/ams:status')

    resultiterator = await hooks.search_search(
        app=request.app, q=full_text_query,
        sortpath=['ams:sort_modified'],
        result_info=result_info,
        facets=facets,
        limit=limit, offset=offset,
        filters=filters, iso_639_1_code='nl'
    )

    ctx = await hooks.mds_context()
    ctx_json = json.dumps(ctx)

    response = web.StreamResponse()
    response.content_type = request['best_content_type']
    response.enable_compression()
    first = True
    await response.prepare(request)
    await response.write(b'{"@context":')
    await response.write(ctx_json.encode())
    await response.write(b',"dcat:dataset":[')

    async for docid, doc in resultiterator:
        canonical_doc = await hooks.mds_canonicalize(app=request.app, data=doc)
        canonical_doc = await hooks.mds_after_storage(app=request.app, data=canonical_doc, doc_id=docid)
        keepers = {'@id', 'dct:identifier', 'dct:title', 'dct:description',
                   'dcat:keyword', 'foaf:isPrimaryTopicOf', 'dcat:distribution',
                   'dcat:theme', 'ams:owner', 'ams:sort_modified'}
        if admin:
            keepers.add('ams:status')
        for key in list(canonical_doc.keys()):
            if key not in keepers:
                del canonical_doc[key]
        keepers = {'dct:format', 'dcat:mediaType', 'ams:resourceType', 'ams:distributionType',
                   'ams:serviceType', 'dc:identifier'}
        for d in canonical_doc.get('dcat:distribution', []):
            for key in list(d.keys()):
                if key not in keepers:
                    del d[key]
        if not first:
            await response.write(b',')
        else:
            first = False
        await response.write(json.dumps(canonical_doc).encode())

    await response.write(b']')
    await response.write(b', "void:documents": ')
    await response.write(str(result_info['/']).encode())
    del result_info['/']
    await response.write(b', "ams:facet_info": ')
    await response.write(json.dumps(result_info).encode())
    await response.write(b'}')
    await response.write_eof()
    return response


async def link_redirect(request: web.Request):
    dataset = request.match_info['dataset']
    distribution = request.match_info['distribution']
    etag_if_none_match = conditional.parse_if_header(
        request, conditional.HEADER_IF_NONE_MATCH
    )
    if etag_if_none_match == '*':
        raise web.HTTPBadRequest(
            body='Endpoint does not support * in the If-None-Match header.'
        )

    try:
        doc, etag = await request.app.hooks.storage_retrieve(
            app=request.app, docid=dataset, etags=etag_if_none_match
        )
    except KeyError:
        raise web.HTTPNotFound()
    if doc is None:
        raise web.HTTPNotModified(headers={'ETag': etag})
    headers = {'ETag': etag}
    resource_url = None
    for dist in doc.get('dcat:distribution', []):
        if dist.get('dc:identifier', None) == distribution:
            resource_url = dist.get('dcat:accessURL', None)
            break
    if resource_url is None:
        raise web.HTTPNotFound(headers=headers)
    raise web.HTTPTemporaryRedirect(location=resource_url, headers=headers)


async def post_collection(request: web.Request):
    if hasattr(request, "authz_subject"):
        subject = request.authz_subject
        scopes = request.authz_scopes
        _logger.warning(f"AUTHZ  subject {subject}, scopes {scopes}")

    hooks = request.app.hooks
    datasets_url = _datasets_url(request)
    # Grab the document from the request body and canonicalize it.
    try:
        doc = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest(text='invalid json')
    canonical_doc = await hooks.mds_canonicalize(app=request.app, data=doc)

    docid = canonical_doc.get('dct:identifier')
    if docid is not None:
        if not re.fullmatch(r"(?:%[a-f0-9]{2}|[-\w:@!$&'()*+,;=.~])+", docid):
            raise web.HTTPBadRequest(
                text="Illegal value for dct:identifier"
            )
        del canonical_doc['dct:identifier']
    else:
        docid = await hooks.storage_id()

    canonical_doc = await hooks.mds_before_storage(app=request.app, data=canonical_doc)
    # Let the metadata plugin grab the full-text search representation
    searchable_text = await hooks.mds_full_text_search_representation(
        data=canonical_doc
    )
    try:
        new_etag = await hooks.storage_create(
            app=request.app, docid=docid, doc=canonical_doc,
            searchable_text=searchable_text, iso_639_1_code="nl"
        )
    except KeyError:
        raise web.HTTPBadRequest(
            text='Document with dct:identifier {} already exists'.format(docid)
        )
    return web.Response(
        status=201, headers={
            'Etag': new_etag,
            'Location': datasets_url + f'/{docid}'
        },
        content_type='text/plain'
    )


def _datasets_url(request: web.Request) -> str:
    return request.app.config['web']['baseurl'] + 'datasets'


def _csv_decode_line(s: str) -> T.Optional[T.Set[str]]:
    reader = csv.reader([s])
    try:
        return set(next(iter(reader)))
    except (csv.Error, StopIteration):
        return None
