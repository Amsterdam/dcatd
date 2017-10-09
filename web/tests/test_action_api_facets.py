import logging, urllib
from unittest import TestCase

from aiohttp.test_utils import make_mocked_request

from datacatalog.action_api import SearchParam, Facet, extract_queryparams
from . import fixtures

log = logging.getLogger(__name__)


class TestExtractQeuryParams(TestCase):
    """
    Unit tests for datacatalog.action_api.extract_queryparams
    """
    def test_facet_fields(self):
        facets, json_data = fixtures.random_facets()
        request = self._get_request(SearchParam.FACET_FIELDS.value, json_data)

        query = extract_queryparams(request)
        self.assertEqual(len(query[SearchParam.FACET_FIELDS]), len(facets))

        for facet in Facet:
            if facet.value in facets:
                self.assertIn(facet.value, query[SearchParam.FACET_FIELDS])
            else:
                self.assertNotIn(facet.value, query[SearchParam.FACET_FIELDS])

    def _get_request(self, queryfield, queryvalue):
        params = {queryfield: queryvalue}
        queryparams = urllib.parse.urlencode(params)
        request = make_mocked_request('GET', f"/?{queryparams}")
        return request

    def test_facet_query(self):
        facets, querystring = fixtures.random_facet_query()
        request = self._get_request(SearchParam.FACET_QUERY.value, querystring)

        query  = extract_queryparams(request)
        self.assertEqual(len(query[SearchParam.FACET_QUERY]), len(facets))

        for facet in Facet:
            if facet.value in facets:
                self.assertIn(facet.value, query[SearchParam.FACET_QUERY])
                self.assertEqual(query[SearchParam.FACET_QUERY][facet.value], facets[facet.value])
            else:
                self.assertNotIn(facet.value, query[SearchParam.FACET_QUERY])
