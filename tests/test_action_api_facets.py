import urllib.parse
import json

from aiohttp.test_utils import make_mocked_request

from datacatalog.action_api import SearchParam, Facet, extract_queryparams


# Unit tests for datacatalog.action_api.extract_queryparams


def _get_request(queryfield, queryvalue):
    params = {queryfield: queryvalue}
    queryparams = urllib.parse.urlencode(params)
    request = make_mocked_request('GET', f"/?{queryparams}")
    return request


def test_facet_fields(random_facets):
    request = _get_request(SearchParam.FACET_FIELDS.value, json.dumps(random_facets))

    query = extract_queryparams(request)
    assert len(query[SearchParam.FACET_FIELDS]) == len(random_facets)

    for facet in Facet:
        if facet.value in random_facets:
            assert facet.value in query[SearchParam.FACET_FIELDS]
        else:
            assert facet.value not in query[SearchParam.FACET_FIELDS]


def test_facet_query(random_facet_query):
    facets, querystring = random_facet_query
    request = _get_request(SearchParam.FACET_QUERY.value, querystring)

    query  = extract_queryparams(request)
    assert len(query[SearchParam.FACET_QUERY]) == len(facets)

    for facet in Facet:
        if facet.value in facets:
            assert facet.value in query[SearchParam.FACET_QUERY]
            assert query[SearchParam.FACET_QUERY][facet.value] == facets[facet.value]
        else:
            assert facet.value not in query[SearchParam.FACET_QUERY]
