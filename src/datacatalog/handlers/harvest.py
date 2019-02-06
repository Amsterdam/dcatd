import json.decoder
# import logging
# import typing as T
# import urllib.parse

from aiohttp import web
# from pyld import jsonld

from aiohttp_extras.content_negotiation import produces_content_types


# logger = logging.getLogger(__name__ )


@produces_content_types('application/ld+json', 'application/json')
async def get_collection(request: web.Request) -> web.StreamResponse:
    # language=rst
    """Handler for ``/datasets``"""
    hooks = request.app.hooks

    admin = False
    if hasattr(request, "authz_scopes"):
        scopes = request.authz_scopes
        if 'CAT/W' in scopes or 'CAT/R' in scopes:
            admin = True

    if admin:
        # show non-available datasets only to admin
        filters = {}
    else:
        filters = {
            '/properties/ams:status': {
                'eq': 'beschikbaar'
            }
        }
    result_info = {}
    dataset_iterator = await hooks.search_search(
        app=request.app, q='',
        sortpath=['ams:sort_modified'],
        result_info=result_info,
        filters=filters, iso_639_1_code='nl'
    )

    ctx = await hooks.mds_context()
    ctx_json = json.dumps(ctx)

    response = web.StreamResponse()
    response.content_type = request['best_content_type']
    response.enable_compression()
    await response.prepare(request)
    await response.write(b'{"@context":')
    await response.write(ctx_json.encode())
    await response.write(b',"dcat:dataset":[')

    separator = b''
    async for docid, doc in dataset_iterator:
        canonical_doc = await hooks.mds_canonicalize(app=request.app, data=doc)
        canonical_doc = await hooks.mds_after_storage(app=request.app, data=canonical_doc, doc_id=docid)
        del canonical_doc['@context']
        await response.write(separator + json.dumps(canonical_doc).encode())
        separator = b','

    await response.write(b']}')
    await response.write_eof()
    return response
