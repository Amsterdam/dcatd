import csv
import json.decoder
# import os.path
import re
import typing as T
# import urllib.parse

from aiohttp import web
from pyld import jsonld

from aiohttp_extras import conditional
from aiohttp_extras.content_negotiation import produces_content_types

from datacatalog import authorization

_DCAT_ID_KEY = '@id'
_DCAT_DCT_ID_KEY = 'http://purl.org/dc/terms/identifier'
_DCAT_DCT_DESCRIPTION_KEY = 'http://purl.org/dc/terms/description'
_DCAT_DCT_ISSUED_KEY = 'http://purl.org/dc/terms/issued'
_DCAT_DCT_TITLE_KEY = 'http://purl.org/dc/terms/title'
_DCAT_DCT_FORMAT_KEY = 'http://purl.org/dc/terms/format'
_DCAT_DCAT_KEYWORD_KEY = 'http://www.w3.org/ns/dcat#keyword'
_DCAT_DCAT_DISTRIBUTION_KEY = 'http://www.w3.org/ns/dcat#distribution'
_FACET_QUERY_KEY = re.compile(
    r'(?:/properties/[^/=~<>]+(?:/items)?)+'
)
_FACET_QUERY_VALUE = re.compile(
    r'(in|eq|gt|lt|ge|le)=(.*)', flags=re.S
)
_COMMA_SEPARATED_SEGMENT = re.compile(
    r'(?:\\.|[^,\\])+'
)
_ESCAPED_CHARACTER = re.compile(r'\\(.)')


def _add_blank_node_identifiers_to(distributions: T.Iterable[dict]) -> None:
    counter = 0
    for distribution in distributions:
        counter += 1
        distribution['@id'] = "_:d{}".format(counter)


@produces_content_types('application/ld+json', 'application/json')
async def get(request: web.Request):
    docid = request.match_info['dataset']
    etag_if_none_match = conditional.parse_if_header(
        request, conditional.HEADER_IF_NONE_MATCH
    )
    if etag_if_none_match == '*':
        raise web.HTTPBadRequest(
            body='Endpoint does not support * in the If-None-Match header.'
        )
    # now we know the etag is either None or a set
    try:
        doc, etag = await request.app.hooks.storage_retrieve(
            app=request.app, docid=docid, etags=etag_if_none_match
        )
    except KeyError:
        raise web.HTTPNotFound()
    if doc is None:
        return web.Response(status=304, headers={'Etag': etag})
    expanded_doc = jsonld.expand(doc)[0]
    canonical_doc = await request.app.hooks.mds_canonicalize(data=expanded_doc, id=docid)
    _add_blank_node_identifiers_to(canonical_doc['dcat:distribution'])
    return web.json_response(canonical_doc, headers={
        'Etag': etag, 'content_type': 'application/ld+json'
    })


@authorization.authorize()
async def put(request: web.Request):
    hooks = request.app.hooks
    # Grab the document from the request body and canonicalize it.
    try:
        doc = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest(text='invalid json')
    canonical_doc = await hooks.mds_canonicalize(data=doc)

    # Make sure the docid in the path corresponds to the ids given in the
    # document, if any. The assumption is that request.path (which corresponds
    # to the path part of the incoming HTTP request) is the path as seen by
    # the client. This is not necessarily true.
    docid = request.match_info['dataset']
    docurl = f"ams-dcatd:{docid}"
    if '@id' in canonical_doc:
        if canonical_doc['@id'] != docurl:
            raise web.HTTPBadRequest(
                text='Invalid @id: {} != {}'.format(
                    canonical_doc['@id'], docurl
                )
            )
        del canonical_doc[_DCAT_ID_KEY]
    if 'dct:identifier' in canonical_doc:
        if canonical_doc['dct:identifier'] != docid:
            raise web.HTTPBadRequest(
                text='Invalid dct:identifier: {} != {}'.format(
                    canonical_doc['dct:identifier'], docid
                )
            )
        del canonical_doc['dct:identifier']
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
            new_etag = await hooks.storage_update(
                app=request.app, docid=docid, doc=canonical_doc,
                searchable_text=searchable_text, etags=etag_if_match,
                iso_639_1_code="nl"
            )
        except ValueError:
            raise web.HTTPPreconditionFailed()
        return web.Response(status=204, headers={'Etag': new_etag})

    # If-None-Match: * is for creates
    if etag_if_none_match != '*':
        raise web.HTTPBadRequest(
            body='For inserts of new documents, provide If-None-Match: *'
        )
    try:
        new_etag = await hooks.storage_create(
            app=request.app, docid=docid, doc=canonical_doc,
            searchable_text=searchable_text, iso_639_1_code="nl"
        )
    except KeyError:
        raise web.HTTPPreconditionFailed()
    return web.Response(
        status=201, headers={'Etag': new_etag}, content_type='text/plain'
    )


@authorization.authorize()
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

    # Extract facet filters:
    filters = {}
    for key in query:
        if not _FACET_QUERY_KEY.fullmatch(key):
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
        limit = int(limit)
    offset = query.get('offset', 0)
    if offset is not None:
        offset = int(offset)

    result_info = {}
    resultiterator = await hooks.search_search(
        app=request.app, q=full_text_query,
        sortproperty=_DCAT_DCT_ISSUED_KEY,
        result_info=result_info,
        facets=[
            '/properties/dcat:distribution/items/properties/ams:resourceType',
            '/properties/dcat:distribution/items/properties/dct:format',
            '/properties/dcat:distribution/items/properties/ams:distributionType',
            '/properties/dcat:distribution/items/properties/dct:serviceType',
            '/properties/dcat:keyword/items',
            '/properties/dcat:theme/items',
            '/properties/ams:owner'
        ],
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
        canonical_doc = await hooks.mds_canonicalize(data=doc, id=docid)
        keepers = {'@id', 'dct:identifier', 'dct:title', 'dct:description',
                   'dcat:keyword', 'foaf:isPrimaryTopicOf', 'dcat:distribution',
                   'dcat:theme', 'ams:owner'}
        for key in list(canonical_doc.keys()):
            if key not in keepers:
                del canonical_doc[key]
        keepers = {'dct:format', 'ams:resourceType', 'ams:distributionType',
                   'ams:serviceType'}
        for d in canonical_doc.get('dcat:distribution', []):
            for key in list(d.keys()):
                if key not in keepers:
                    del d[key]
        if not first:
            await response.write(b',')
        else:
            first = False
        await response.write(json.dumps(canonical_doc).encode())

    # make sure facet filters are sorted by value


    await response.write(b']')
    await response.write(b', "void:documents": ')
    await response.write(str(result_info['/']).encode())
    del result_info['/']
    await response.write(b', "ams:facet_info": ')
    await response.write(json.dumps(result_info).encode())
    await response.write(b'}')
    await response.write_eof()
    return response


@authorization.authorize()
async def post_collection(request: web.Request):
    hooks = request.app.hooks
    datasets_url = _datasets_url(request)
    # Grab the document from the request body and canonicalize it.
    try:
        doc = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest(text='invalid json')
    canonical_doc = await hooks.mds_canonicalize(data=doc)

    docurl = canonical_doc.get('@id')
    if docurl is not None:
        del canonical_doc['@id']

    docid = canonical_doc.get('dct:identifier')
    if docid is not None:
        del canonical_doc['dct:identifier']

    if docid is not None:
        collection_url_plus_docid = f"ams-dcatd:{docid}"
        if docurl is None:
            docurl = collection_url_plus_docid
        elif docurl != collection_url_plus_docid:
            raise web.HTTPBadRequest(
                text='{} != {}'.format(docurl, collection_url_plus_docid)
            )
    elif docurl is not None:
        if docurl.find(datasets_url + '/') != 0:
            raise web.HTTPBadRequest(
                text=f"{_DCAT_ID_KEY} must start with {datasets_url}/"
            )
        docid = docurl[len(datasets_url) + 1:]
        if not re.fullmatch(r"(?:%[a-f0-9]{2}|[-\w:@!$&'()*+,;=.~])+", docid):
            raise web.HTTPBadRequest(
                text=f"Illegal value for {_DCAT_ID_KEY}"
            )
    else:
        docid = await hooks.storage_id()
        docurl = f"{datasets_url}/{docid}"
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
            text='Document with id {} already exists'.format(docid)
        )
    return web.Response(
        status=201, headers={'Etag': new_etag, 'Location': docurl},
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


def _split_comma_separated_stringset(s: str) -> T.Optional[T.Set[str]]:
    pos = 0
    len_s = len(s)
    retval = set()
    while pos < len_s:
        if pos != 0 and s[pos] == ',':
            pos = pos + 1
        matches: T.List[str] = _COMMA_SEPARATED_SEGMENT.match(s, pos)
        if matches is None:
            return None
        match = matches[0]
        pos = pos + len(match)
        retval.add(_ESCAPED_CHARACTER.sub(r'\1', match))
    return retval
