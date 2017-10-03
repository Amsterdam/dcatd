from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from datacatalog import app
from . import fixtures

FIXTURE_IDS = ['62513382-3b26-4bc8-9096-40b6ce8383c0',
               '17be64bb-da74-4195-9bb8-565c39846af2',
               '9c3036b8-f6ac-4a4e-9036-5a3cc90c3900']
FIXTURE_NAMES = ["100-validated-species-of-plants",
                 "1617in10-regulation-of-sale-of-overseas-properties-20170426-c",
                 "2016-regione-asia-est-oceania-classi-di-eta"]


class TestActionAPI(AioHTTPTestCase):
    async def get_application(self):
        return app.get_app()

    @unittest_run_loop
    async def test_show(self):
        for fixture_id in FIXTURE_IDS:
            resp = await self.client.get(f'/datacatalog/api/3/action/package_show?id={fixture_id}')
            assert resp.status == 200
            text = await resp.text()
            assert fixture_id in text

    @unittest_run_loop
    async def test_show_no_id(self):
        resp = await self.client.get(f'/datacatalog/api/3/action/package_show')
        assert resp.status == 400

    @unittest_run_loop
    async def test_search(self):
        resp = await self.client.get('/datacatalog/api/3/action/package_search')
        assert resp.status == 200
        text = await resp.text()
        for fixture_id in FIXTURE_IDS:
            assert fixture_id in text

    @unittest_run_loop
    async def test_list(self):
        resp = await self.client.get('/datacatalog/api/3/action/package_list')
        assert resp.status == 200
        text = await resp.text()

        for name in FIXTURE_NAMES:
            assert name in text

    @unittest_run_loop
    async def test_non_existent_action(self):
        non_existent = fixtures.random_string()
        resp = await self.client.get(f'/datacatalog/api/3/action/{non_existent}')
        assert resp.status == 404
