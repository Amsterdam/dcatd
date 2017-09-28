from aiohttp import web

"""
    Handle the index request
"""
async def handle(request):
    text = "Hello, World! This is the datacatalog"
    return web.Response(text=text)
