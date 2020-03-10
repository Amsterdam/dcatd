import asyncio
import os

from aiohttp import web
import uvloop

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from datacatalog import application


def main():
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment="dcatd",
            integrations=[AioHttpIntegration()],
            ignore_errors=['HTTPTemporaryRedirect']
    )

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    aio_app = application.Application()
    web.run_app(aio_app, port=aio_app.config['web']['port'])
    return 0


if __name__ == '__main__':
    main()
