import os
import json
import logging
import copy

from datacatalog import action_api

log = logging.getLogger(__name__)


class AbstractSearch:
    def is_healthy(self):
        pass

    def search(self, query={}):
        pass


class InMemorySearch(AbstractSearch):
    FILEDATA_PATH = "/app/data/packages.json"

    def __init__(self):
        if self.is_healthy():
            with open(self.FILEDATA_PATH) as json_data:
                self.all_packages = json.load(json_data)

    def is_healthy(self):
        return os.path.exists(self.FILEDATA_PATH)

    def _result_matches_facets(self, result, query):
        if action_api.SearchParam.FACET_QUERY not in query:
            return True

        facets = query[action_api.SearchParam.FACET_QUERY]
        if action_api.Facet.GROUP.value in facets:
            group_match = False
            for group in result['groups']:
                if group['name'] == facets[action_api.Facet.GROUP.value]:
                    group_match = True
            if not group_match:
                return False

        if action_api.Facet.RESOURCE.value in facets:
            resource_match = False
            for resource in result['resources']:
                if resource['format'] == facets[action_api.Facet.RESOURCE.value]:
                    resource_match = True
            if not resource_match:
                return False

        if action_api.Facet.PUBLISHER.value in facets:
            if result['organization'] is None or \
               result['organization']['name'] != facets[action_api.Facet.PUBLISHER.value]:
                return False

        return True

    def search(self, query={}):
        results = copy.deepcopy(self.all_packages)

        filtered_results = []
        for possible_result in results['result']['results']:
            if self._result_matches_facets(possible_result, query):
                filtered_results.append(possible_result)
        results['result']['results'] = filtered_results

        if action_api.SearchParam.FACET_FIELDS in query:
            output_facets = {}
            output_searchfacets = {}
            for requested_facet in query[action_api.SearchParam.FACET_FIELDS]:
                output_facets[requested_facet] = results['result']['facets'][requested_facet]
                output_searchfacets[requested_facet] = results['result']['search_facets'][requested_facet]
            results['result']['facets'] = output_facets
            results['result']['search_facets'] = output_searchfacets

        begin = query[action_api.SearchParam.START] if action_api.SearchParam.START in query else 0
        if action_api.SearchParam.ROWS in query:
            end = begin + query[action_api.SearchParam.ROWS]
            results['result']['results'] =  results['result']['results'][begin:end]
        else:
            results['result']['results'] = results['result']['results'][begin:]

        return results


def is_healthy():
    return implemented_serach.is_healthy()


def search(query={}):
    return implemented_serach.search(query)


implemented_serach = InMemorySearch()
