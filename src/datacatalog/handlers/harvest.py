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
    dataset_iterator = await hooks.storage_all(app=request.app)

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
    async for docid, _etag, doc in dataset_iterator:
        canonical_doc = await hooks.mds_canonicalize(data=doc, id=docid)
        await response.write(separator + json.dumps(canonical_doc).encode())
        separator = b','

    await response.write(b']}')
    await response.write_eof()
    return response
