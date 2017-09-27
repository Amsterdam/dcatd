from aiohttp import web
import systemhealth

async def handle(request):
    text = "Hello, World! This is the datacatalog"
    return web.Response(text=text)

app = web.Application()
app.router.add_get('/', handle)
app.router.add_get('/system/health', systemhealth.handle)

web.run_app(app, port=8000)
