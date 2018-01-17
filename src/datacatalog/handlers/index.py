from aiohttp import web


async def handle(request):
    # language=rst
    """Handle the index request"""
    text = "Hello, World! This is the datacatalog"
    return web.Response(text=text)
