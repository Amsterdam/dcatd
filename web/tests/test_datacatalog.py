from unittest import mock

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from datacatalog import app


class TestDatacatalog(AioHTTPTestCase):
    async def get_application(self):
        return app.get_app()

    @unittest_run_loop
    async def test_index(self):
        resp = await self.client.get('/')
        assert resp.status == 200
        text = await resp.text()
        assert 'Hello, World' in text

    @unittest_run_loop
    async def test_health_ok(self):
        resp = await self.client.get('/system/health')
        assert resp.status == 200
        text = await resp.text()
        assert 'systemhealth is OK' in text

    @mock.patch('datacatalog.datastore.is_healthy', side_effect=lambda:False)
    @unittest_run_loop
    async def test_health_not_ok_datastore(self, mock):
        resp = await self.client.get('/system/health')
        assert resp.status == 500

    @mock.patch('datacatalog.search.is_healthy', side_effect=lambda:False)
    @unittest_run_loop
    async def test_health_not_ok_datastore(self, mock):
        resp = await self.client.get('/system/health')
        assert resp.status == 500
