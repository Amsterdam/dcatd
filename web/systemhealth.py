from aiohttp import web

"""
    Handle the system health check
    
    Any failure in the systems that the catalog depends upon should result in a status 500
    If all systems are go status 200 is returned
"""
async def handle(request):
    text = "Datacatalog-core systemhealth is OK"
    return web.Response(text=text)
