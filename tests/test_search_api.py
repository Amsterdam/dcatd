import json
import logging
import urllib.parse

import pytest

from datacatalog import application
from datacatalog.handlers.action_api import Facet, SearchParam

logger = logging.getLogger(__name__)


async def get_application(dcat_client):
    return application.Application()


async def _get_response(dcat_client, queryfield, queryvalue):
    params = {queryfield: queryvalue}
    return await _get_response_params(dcat_client, params)


async def _get_response_params(dcat_client, params):
    query = urllib.parse.urlencode(params)
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_search?{query}')
    return resp


async def _assert_number_of_results(resp, amount):
    assert resp.status == 200
    text = await resp.text()
    results = json.loads(text)
    assert len(results['result']['results']) == amount


async def test_search(dcat_client, all_packages):
    resp = await dcat_client.get('/datacatalog/api/3/action/package_search')
    assert resp.status == 200
    text = await resp.text()
    results = json.loads(text)
    assert len(results['result']['results']) == len(all_packages)


@pytest.mark.parametrize("start,expected", [
    ('1', 2),
    ('2', 1),
    ('100', 0),
])
async def test_search_start(dcat_client, start, expected):
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_search?start={start}')
    assert resp.status == 200
    text = await resp.text()
    results = json.loads(text)


@pytest.mark.parametrize("start", ['-1', 'a'])
async def test_search_start_invalid(dcat_client, start):
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_search?start={start}')
    assert resp.status == 400


@pytest.mark.parametrize("rows,expected", [
    ('1', 1),
    ('3', 3),
    ('100', 3),
])
async def test_search_rows(dcat_client, rows, expected):
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_search?rows={rows}')
    assert resp.status == 200
    text = await resp.text()
    results = json.loads(text)
    assert len(results['result']['results']) == expected


@pytest.mark.parametrize("rows", ['a', '0'])
async def test_search_rows_invalid(dcat_client, rows):
    # 400 or 200 OK with error?
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_search?rows={rows}')
    assert resp.status == 400


async def test_select_facets(dcat_client, random_facets):
    resp = await _get_response(dcat_client, SearchParam.FACET_FIELDS.value, json.dumps(random_facets))

    assert resp.status == 200
    text = await resp.text()
    results = json.loads(text)
    assert len(results['result']['facets']) == len(random_facets)
    for facet in Facet:
        if facet.value in random_facets:
            assert facet.value in results['result']['facets']
        else:
            assert facet.value not in results['result']['facets']


@pytest.mark.parametrize('query,results', [
    ('res_format:"PDF"', 1),
    ('organization:"sdb"', 1),
    ('organization:"sdb" res_format:"CSV"', 1),
    ('res_format:"CSV"', 2),
    ('organization:"non-existent"', 0),
    ('res_format:"non-existent"', 0),
])
async def test_filter_facets(dcat_client, query, results):
    resp = await _get_response(dcat_client, SearchParam.FACET_QUERY.value, query)
    await _assert_number_of_results(resp, results)


@pytest.mark.parametrize('facets', [
    {'groups', 'res_format', 'organization'},
    {'groups'}
])
async def test_facet_fields(dcat_client, facets: set):
    query = '[' + ','.join(f'"{x}"' for x in facets) + ']'
    resp = await _get_response(dcat_client, SearchParam.FACET_FIELDS.value, query)
    await _assert_number_of_results(resp, 3)

    text = await resp.text()
    results = json.loads(text)

    assert len(results['result']['facets']) == len(facets)
    assert set(results['result']['facets']) == facets


@pytest.mark.parametrize('facets', [
    {'groups', 'res_format', 'organization'},
    {'res_format'}
])
async def test_searchfacet_fields(dcat_client, facets):
    query = '[' + ','.join(f'"{x}"' for x in facets) + ']'
    resp = await _get_response(dcat_client, SearchParam.FACET_FIELDS.value, query)
    await _assert_number_of_results(resp, 3)

    text = await resp.text()
    results = json.loads(text)

    assert len(results['result']['search_facets']) == len(facets)
    assert set(results['result']['search_facets']) == facets


async def test_facets_field_query0(dcat_client):
    params = {
        SearchParam.FACET_FIELDS.value: '["res_format","organization"]',
        SearchParam.FACET_QUERY.value: 'res_format:"PDF"'
    }
    resp = await _get_response_params(dcat_client, params)
    await _assert_number_of_results(resp, 1)

    text = await resp.text()
    results = json.loads(text)

    assert len(results['result']['facets']) == 2
    assert len(results['result']['search_facets']) == 2

    assert len(results['result']['facets']['organization']) == 0
    assert len(results['result']['search_facets']['organization']['items']) == 0

    assert len(results['result']['facets']['res_format']) == 1
    assert len(results['result']['search_facets']['res_format']['items']) == 1

    assert results['result']['facets']['res_format']['PDF'] == 1
    assert results['result']['search_facets']['res_format']['items'][0]['count'] == 1
    assert results['result']['search_facets']['res_format']['items'][0]['name'] == 'PDF'


async def test_facets_field_query1(dcat_client):
    params = {
        SearchParam.FACET_FIELDS.value: '["res_format","organization"]',
        SearchParam.FACET_QUERY.value: 'organization:"sdb" res_format:"CSV"'
    }
    resp = await _get_response_params(dcat_client, params)
    await _assert_number_of_results(resp, 1)

    text = await resp.text()
    results = json.loads(text)

    assert len(results['result']['facets']) == 2
    assert len(results['result']['search_facets']) == 2

    assert len(results['result']['facets']['organization']) == 1
    assert len(results['result']['search_facets']['organization']['items']) == 1

    assert results['result']['facets']['organization']['sdb'] == 1
    assert results['result']['search_facets']['organization']['items'][0]['count'] == 1
    assert results['result']['search_facets']['organization']['items'][0]['name'] == 'sdb'

    assert results['result']['facets']['res_format']['CSV'] == 1
    assert results['result']['search_facets']['res_format']['items'][0]['count'] == 1
    assert results['result']['search_facets']['res_format']['items'][0]['name'] == 'CSV'


@pytest.mark.parametrize(
    'query,id', [
        ("oceania", '17be64bb-da74-4195-9bb8-565c39846af2'),
        ("machine learning", '62513382-3b26-4bc8-9096-40b6ce8383c0')
    ],
    ids=lambda x: x[0]
)
async def test_fulltext_query1(dcat_client, query, id):
    resp = await _get_response(dcat_client, SearchParam.QUERY.value, query)
    await _assert_number_of_results(resp, 1)

    text = await resp.text()
    results = json.loads(text)
    assert results['result']['results'][0]['id'] == id


@pytest.mark.parametrize(
    'query,id', [
        ("machines", '62513382-3b26-4bc8-9096-40b6ce8383c0'),  # find 'machine'
        ("plant",    '62513382-3b26-4bc8-9096-40b6ce8383c0')   # find 'plants'
    ],
    ids=lambda x: x[0]
)
async def test_fulltext_query_variations(dcat_client, query, id):
    resp = await _get_response(dcat_client, SearchParam.QUERY.value, query)  # find 'machine'
    await _assert_number_of_results(resp, 1)

    text = await resp.text()
    results = json.loads(text)
    assert results['result']['results'][0]['id'] == id
