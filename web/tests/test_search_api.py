import json
import urllib

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from datacatalog import app
from datacatalog.action_api import Facet, SearchParam

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

    @unittest_run_loop
    async def test_select_facets(self):
        facets, json_data = fixtures.random_facets()
        resp = await self._get_response(SearchParam.FACET_FIELDS.value, json_data)

        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['facets']) == len(facets)
        for facet in Facet:
            if facet.value in facets:
                assert facet.value in results['result']['facets']
            else:
                assert facet.value not in results['result']['facets']

    async def _get_response(self, queryfield, queryvalue):
        params = {queryfield: queryvalue}
        queryparams = urllib.parse.urlencode(params)
        resp = await self.client.get(f'/datacatalog/api/3/action/package_search?{queryparams}')
        return resp

    @unittest_run_loop
    async def test_filter_facets1(self):
        querystring1 = 'res_format:"PDF"'
        querystring2 = 'organization:"sdb"'
        querystring3 = 'organization:"sdb" res_format:"CSV"'

        resp = await self._get_response(SearchParam.FACET_QUERY.value, querystring1)
        await self._assert_less_results(resp, 1)

        resp = await self._get_response(SearchParam.FACET_QUERY.value, querystring2)
        await self._assert_less_results(resp, 1)

        resp = await self._get_response(SearchParam.FACET_QUERY.value, querystring3)
        await self._assert_less_results(resp, 1)

    async def _assert_less_results(self, resp, amount):
        assert resp.status == 200
        text = await resp.text()
        results = json.loads(text)
        assert len(results['result']['results']) == amount

    @unittest_run_loop
    async def test_filter_facets2(self):
        querystring = 'res_format:"CSV"'
        resp = await self._get_response(SearchParam.FACET_QUERY.value, querystring)
        await self._assert_less_results(resp, 2)

    @unittest_run_loop
    async def test_filter_facets0(self):
        querystring = 'organization:"non-existent"'
        resp = await self._get_response(SearchParam.FACET_QUERY.value, querystring)
        await self._assert_less_results(resp, 0)

        querystring = 'res_format:"non-existent"'
        resp = await self._get_response(SearchParam.FACET_QUERY.value, querystring)
        await self._assert_less_results(resp, 0)
