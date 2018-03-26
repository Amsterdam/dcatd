import csv
import json.decoder
import os.path
import re
import typing as T
import urllib.parse

from aiohttp import web
from pyld import jsonld

from datacatalog import authorization
from aiohttp_extras import conditional
from aiohttp_extras.content_negotiation import produces_content_types

_DCAT_ID_KEY = '@id'
_DCAT_DCT_ID_KEY = 'http://purl.org/dc/terms/identifier'
_DCAT_DCT_DESCRIPTION_KEY = 'http://purl.org/dc/terms/description'
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
            docid=docid, etags=etag_if_none_match
        )
    except KeyError:
        raise web.HTTPNotFound()
    if doc is None:
        return web.Response(status=304, headers={'Etag': etag})
    expanded_doc = jsonld.expand(doc)[0]
    docurl = _resource_url(request)
    expanded_doc[_DCAT_ID_KEY] = docurl
    expanded_doc[_DCAT_DCT_ID_KEY] = [{'@value': docid}]
    cannonical_doc = await request.app.hooks.mds_canonicalize(data=expanded_doc)
    _add_blank_node_identifiers_to(cannonical_doc['dcat:distribution'])
    return web.json_response(cannonical_doc, headers={
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
    cannonical_doc = await hooks.mds_canonicalize(data=doc)

    # Make sure the docid in the path corresponds to the ids given in the
    # document, if any. The assumption is that request.path (which corresponds
    # to the path part of the incoming HTTP request) is the path as seen by
    # the client. This is not necessarily true.
    docurl = _resource_url(request)
    docid = request.match_info['dataset']
    expanded_doc = jsonld.expand(cannonical_doc)[0]
    if _DCAT_ID_KEY in expanded_doc:
        if expanded_doc[_DCAT_ID_KEY] != docurl:
            raise web.HTTPBadRequest(
                text='Invalid {}: {} != {}'.format(
                    _DCAT_ID_KEY, expanded_doc[_DCAT_ID_KEY], docurl
                )
            )
        del expanded_doc[_DCAT_ID_KEY]
    if _DCAT_DCT_ID_KEY in expanded_doc:
        if expanded_doc[_DCAT_DCT_ID_KEY][0]['@value'] != docid:
            raise web.HTTPBadRequest(
                text='Invalid {}: {} != {}'.format(
                    _DCAT_DCT_ID_KEY, expanded_doc[_DCAT_DCT_ID_KEY], docid
                )
            )
        del expanded_doc[_DCAT_DCT_ID_KEY]
    # recompute the canonnical doc
    cannonical_doc = await hooks.mds_canonicalize(data=expanded_doc)
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
                docid=docid, doc=cannonical_doc, searchable_text=searchable_text,
                etags=etag_if_match, iso_639_1_code="nl"
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
            docid=docid, doc=cannonical_doc, searchable_text=searchable_text,
            iso_639_1_code="nl"
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
        await request.app.hooks.storage_delete(docid=given_id, etags=etag_if_match)
    except KeyError:
        raise web.HTTPNotFound()
    return web.Response(status=204, content_type='text/plain')


@produces_content_types('application/ld+json', 'application/json')
async def get_collection(request: web.Request) -> web.Response:
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
        match = _FACET_QUERY_VALUE.fullmatch(query[key])
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
    offset = query.get('offset', None)
    if offset is not None:
        offset = int(offset)

    resultiterator = hooks.search_search(
        q=full_text_query, limit=limit, offset=offset, filters=filters,
        iso_639_1_code='nl'
    )

    collection_url = _resource_url(request) + '/'
    ctx = await hooks.mds_context()
    ctx_json = json.dumps(ctx)

    response = web.StreamResponse()
    response.content_type = 'application/json'
    response.enable_compression()
    first = True
    await response.prepare(request)
    await response.write(b'{"@context":')
    await response.write(ctx_json.encode())
    await response.write(b',"dcat:dataset":[')

    async for docid, doc in await resultiterator:
        expanded_doc = jsonld.expand(doc)[0]
        docurl = urllib.parse.urljoin(collection_url, docid)
        resultdoc = {
            _DCAT_ID_KEY: docurl,
            _DCAT_DCT_ID_KEY: [{'@value': docid}],
            _DCAT_DCT_TITLE_KEY: expanded_doc.get(_DCAT_DCT_TITLE_KEY, ''),
            _DCAT_DCT_DESCRIPTION_KEY: expanded_doc.get(_DCAT_DCT_DESCRIPTION_KEY, ''),
            _DCAT_DCAT_KEYWORD_KEY: expanded_doc.get(_DCAT_DCAT_KEYWORD_KEY, []),
            _DCAT_DCAT_DISTRIBUTION_KEY: [
                {_DCAT_DCT_FORMAT_KEY: d[_DCAT_DCT_FORMAT_KEY]}
                for d in expanded_doc.get(_DCAT_DCAT_DISTRIBUTION_KEY, [])
            ]
        }
        compacted_doc = jsonld.compact(resultdoc, ctx)
        del compacted_doc['@context']
        if not first:
            await response.write(b',')
        else:
            first = False
        await response.write(json.dumps(compacted_doc).encode())

    await response.write(b']}')
    await response.write_eof()
    return response


@authorization.authorize()
async def post_collection(request: web.Request):
    hooks = request.app.hooks
    # Grab the document from the request body and canonicalize it.
    try:
        doc = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest(text='invalid json')
    collection_url = _resource_url(request) + '/'
    cannonical_doc = await hooks.mds_canonicalize(data=doc)
    try:
        expanded_doc = jsonld.expand(cannonical_doc)[0]
    except IndexError:
        raise web.HTTPBadRequest(
            text='Must upload a valid document'
        )
    docid = None
    docurl = None
    if _DCAT_ID_KEY in expanded_doc:
        docurl = expanded_doc[_DCAT_ID_KEY]
        del expanded_doc[_DCAT_ID_KEY]
    if _DCAT_DCT_ID_KEY in expanded_doc:
        docid = expanded_doc[_DCAT_DCT_ID_KEY]
        del expanded_doc[_DCAT_DCT_ID_KEY]
    if docid is not None:
        docid = docid[0]['@value']
        if docurl is not None:
            collection_url_plus_docid = urllib.parse.urljoin(collection_url, docid)
            if docurl != collection_url_plus_docid:
                raise web.HTTPBadRequest(
                    text='{} != {}'.format(docurl, collection_url_plus_docid)
                )
    elif docurl is not None:
        path = urllib.parse.urlparse(docurl).path
        if path == '':
            raise web.HTTPBadRequest(
                text='{} must be a URL'.format(_DCAT_ID_KEY)
            )
        docid = os.path.basename(os.path.normpath(path))
    else:
        docid = await hooks.storage_id()
        docurl = urllib.parse.urljoin(collection_url, docid)
    # recompute the canonnical doc
    cannonical_doc = await hooks.mds_canonicalize(data=expanded_doc)
    # Let the metadata plugin grab the full-text search representation
    searchable_text = await hooks.mds_full_text_search_representation(
        data=cannonical_doc
    )
    try:
        new_etag = await hooks.storage_create(
            docid=docid, doc=cannonical_doc, searchable_text=searchable_text,
            iso_639_1_code="nl"
        )
    except KeyError:
        raise web.HTTPBadRequest(
            text='Document with id {} already exists'.format(docid)
        )
    return web.Response(
        status=201, headers={'Etag': new_etag, 'Location': docurl},
        content_type='text/plain'
    )


def _resource_url(request):
    baseurl = request.app.config['web']['baseurl']
    parsed_baseurl = urllib.parse.urlparse(baseurl)
    root = baseurl[:-len(parsed_baseurl.path)] + '/'
    return urllib.parse.urljoin(root, request.path)


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
        match = _COMMA_SEPARATED_SEGMENT.match(s, pos)
        if match is None:
            return None
        match = match[0]
        pos = pos + len(match)
        retval.add(_ESCAPED_CHARACTER.sub(r'\1', match))
    return retval
