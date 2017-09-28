from aiohttp import web

from datacatalog import systemhealth, index

"""
    Construct the the application  
"""
app = web.Application()
app.router.add_get('/', index.handle)
app.router.add_get('/system/health', systemhealth.handle)
