import os
from os import path
from aiohttp.test_utils import AioHTTPTestCase
from datacatalog import application


class BaseTestCase(AioHTTPTestCase):
    _WORKING_PATH = path.dirname(path.abspath(__file__))

    async def get_application(self):
        os.environ['CONFIG_PATH'] = self._WORKING_PATH + path.sep + 'integration_config.yml'
        return application.Application()
