import json

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from datacatalog import app
from . import fixtures


class TestActionAPI(AioHTTPTestCase):
    async def get_application(self):
        return app.get_app()

    @unittest_run_loop
    async def test_show(self):
        for fixture_id in fixtures.FIXTURE_IDS:
            resp = await self.client.get(f'/datacatalog/api/3/action/package_show?id={fixture_id}')
            assert resp.status == 200
            text = await resp.text()
            assert fixture_id in text

    @unittest_run_loop
    async def test_show_by_name(self):
        for name in fixtures.FIXTURE_NAMES:
            resp = await self.client.get(f'/datacatalog/api/3/action/package_show?id={name}')
            assert resp.status == 200
            text = await resp.text()
            object = json.loads(text)
            assert object['result']['id'] in fixtures.FIXTURE_IDS

    @unittest_run_loop
    async def test_show_no_id(self):
        resp = await self.client.get(f'/datacatalog/api/3/action/package_show')
        assert resp.status == 400

    @unittest_run_loop
    async def test_search(self):
        resp = await self.client.get('/datacatalog/api/3/action/package_search')
        assert resp.status == 200
        text = await resp.text()
        for fixture_id in fixtures.FIXTURE_IDS:
            assert fixture_id in text

    @unittest_run_loop
    async def test_list(self):
        resp = await self.client.get('/datacatalog/api/3/action/package_list')
        assert resp.status == 200
        text = await resp.text()

        for name in fixtures.FIXTURE_NAMES:
            assert name in text

    @unittest_run_loop
    async def test_non_existent_action(self):
        non_existent = fixtures.random_string()
        resp = await self.client.get(f'/datacatalog/api/3/action/{non_existent}')
        assert resp.status == 404