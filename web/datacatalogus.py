from aiohttp import web

async def handle(request):
    text = "Hello, World! This is the datacatalogus"
    return web.Response(text=text)

app = web.Application()
app.router.add_get('/', handle)

web.run_app(app, port=8000)