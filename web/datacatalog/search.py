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

        begin = query[action_api.SearchParams.START] if action_api.SearchParams.START in query else 0
        if action_api.SearchParams.ROWS in query:
            end = begin + query[action_api.SearchParams.ROWS]
            results['result']['results'] =  results['result']['results'][begin:end]
        else:
            results['result']['results'] = results['result']['results'][begin:]

        return results


def is_healthy():
    return implemented_serach.is_healthy()


def search(query={}):
    return implemented_serach.search(query)


implemented_serach = InMemorySearch()
