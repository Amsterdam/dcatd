from aiohttp import web


async def handle(request):
    # language=rst
    """Produce the OpenAPI3 definition of this service."""
    text = "Hello, World! This is the datacatalog"
    return web.Response(text=text)
