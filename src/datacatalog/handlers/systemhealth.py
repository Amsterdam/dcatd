from aiohttp import web


async def get(request):
    # language=rst
    """Handle the system health check.

    Any failure in the systems that the catalog depends upon should result in a
    status ``503`` (ie. raise `~aiohttp.web.HTTPServiceUnavailable`). If all
    systems are go status ``200`` is returned

    """
    errors = []
    for result in await request.app.hooks.health_check():
        try:
            value = result.value
            if value is not None:
                errors.append(str(value))
        except Exception as e:
            errors.append(str(e))
    if len(errors) > 0:
        raise web.HTTPServiceUnavailable(
            text="\n".join(errors)
        )

    text = "Datacatalog-core systemhealth is OK"
    return web.Response(text=text)
