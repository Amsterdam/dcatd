from aiohttp import web


async def get(request: web.Request):
    # language=rst
    """Handle the index request"""
    text = "Hello, World! This is the datacatalog"
    return web.Response(text=text)
