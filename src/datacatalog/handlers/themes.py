from aiohttp import web
from aiohttp_extras.content_negotiation import produces_content_types


@produces_content_types('application/json')
async def get(request: web.Request):
    await request.app.hooks.storage_get_from_doc('/properties/', distinct=True)
