import csv
import json.decoder
import re
import typing as T
import urllib.parse

from aiohttp import web_exceptions, web
from pyld import jsonld

from aiohttp_extras import conditional
from aiohttp_extras.content_negotiation import produces_content_types

_DCAT_ID_KEY = '@id'
_DCAT_DC_ID_KEY = 'http://purl.org/dc/terms/identifier'
_DCAT_DC_DESCRIPTION_KEY = 'http://purl.org/dc/terms/description'
_DCAT_DC_TITLE_KEY = 'http://purl.org/dc/terms/title'
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
    expanded_doc = jsonld.expand(doc)[0]
    docurl = _resource_url(request)
    expanded_doc[_DCAT_ID_KEY] = docurl
    expanded_doc[_DCAT_DC_ID_KEY] = [{'@value': docid}]
    cannonical_doc = await request.app.hooks.mds_canonicalize(data=expanded_doc)
    return web.json_response(cannonical_doc, headers={
        'Etag': etag, 'content_type': 'application/ld+json'
    })


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
    docurl = _resource_url(request)
    docid = request.match_info['dataset']
    expanded_doc = jsonld.expand(cannonical_doc)[0]
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

    resultiterator = hooks.search_search(
        q=full_text_query, limit=None, offset=None, filters=filters,
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
            _DCAT_DC_ID_KEY: [{'@value': docid}],
            _DCAT_DC_TITLE_KEY: expanded_doc.get(_DCAT_DC_TITLE_KEY, ''),
            _DCAT_DC_DESCRIPTION_KEY: expanded_doc.get(_DCAT_DC_DESCRIPTION_KEY, ''),
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


async def post_collection(request: web.Request):
    ...


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
