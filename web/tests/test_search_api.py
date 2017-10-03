import json

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from datacatalog import app
from . import fixtures


class TestSearchAPI(AioHTTPTestCase):
    async def get_application(self):
        return app.get_app()

    @unittest_run_loop
    async def test_search(self):
        resp = await self.client.get('/datacatalog/api/3/action/package_search')
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == 3

    @unittest_run_loop
    async def test_search_start(self):
        resp = await self.client.get('/datacatalog/api/3/action/package_search?start=1')
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == 2

        resp = await self.client.get('/datacatalog/api/3/action/package_search?start=2')
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == 1

        resp = await self.client.get('/datacatalog/api/3/action/package_search?start=100')
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == 0

        # 400 or 200 OK with error?
        resp = await self.client.get('/datacatalog/api/3/action/package_search?start=-1')
        assert resp.status == 400

        resp = await self.client.get('/datacatalog/api/3/action/package_search?start=a')
        assert resp.status == 400

    @unittest_run_loop
    async def test_search_rows(self):
        resp = await self.client.get('/datacatalog/api/3/action/package_search?rows=1')
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == 1

        random_length = fixtures.random_int(3)
        resp = await self.client.get(f'/datacatalog/api/3/action/package_search?rows={random_length}')
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == random_length

        resp = await self.client.get('/datacatalog/api/3/action/package_search?rows=100')
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == 3

        # 400 or 200 OK with error?
        resp = await self.client.get('/datacatalog/api/3/action/package_search?rows=a')
        assert resp.status == 400

        resp = await self.client.get('/datacatalog/api/3/action/package_search?rows=0')
        assert resp.status == 400
