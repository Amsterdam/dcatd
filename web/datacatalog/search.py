import os
import json
import logging
import copy
from functools import reduce

from datacatalog import action_api

log = logging.getLogger(__name__)


class AbstractSearch:
    async def is_healthy(self):
        pass

    async def search(self, query={}):
        pass


def _init_or_increment(dictionary, key):
    if key in dictionary:
        dictionary[key] += 1
    else:
        dictionary[key] = 1


def _matcher(key, value):
    def _reduce_function(seed, dictionary):
        return seed or value is None or dictionary[key] == value
    return _reduce_function


class InMemorySearch(AbstractSearch):
    FILEDATA_PATH = "/app/data/packages.json"

    def __init__(self):
        if self.is_healthy():
            with open(self.FILEDATA_PATH) as json_data:
                self.all_packages = json.load(json_data)

    async def is_healthy(self):
        return os.path.exists(self.FILEDATA_PATH)

    def _result_matches_facets(self, result, query):
        if action_api.SearchParam.FACET_QUERY not in query:
            return True

        facets = query[action_api.SearchParam.FACET_QUERY]

        if action_api.Facet.GROUP.value in facets:
            match_function = _matcher('name', facets[action_api.Facet.GROUP.value])
            group_match = reduce(match_function, result['groups'], False)
            if not group_match:
                return False

        if action_api.Facet.RESOURCE.value in facets:
            match_function = _matcher('format', facets[action_api.Facet.RESOURCE.value])
            resource_match = reduce(match_function, result['resources'], False)
            if not resource_match:
                return False

        if action_api.Facet.PUBLISHER.value in facets:
            if result['organization'] is None or \
               result['organization']['name'] != facets[action_api.Facet.PUBLISHER.value]:
                return False

        return True

    def _get_empty_facets(self):
        return {facet.value: {} for facet in action_api.Facet}

    def _get_empty_search_facets(self):
        return {
            facet.value: {"items": [], "title": facet.value}
            for facet in action_api.Facet
        }

    def _get_facets(self, facets, result):
        if result['organization'] is not None:
            _init_or_increment(facets['organization'], result['organization']['name'])

        for resource in result['resources']:
            _init_or_increment(facets['res_format'], resource['format'])

        for group in result['groups']:
            _init_or_increment(facets['groups'], group['name'])

        return facets

    def _add_to_items_or_increment(self, items, candidate_item, name_key, title_key):
        for item in items["items"]:
            if item["name"] == candidate_item[name_key]:
                item["count"] += 1
                return

        items["items"].append({
            "count": 1,
            "display_name": candidate_item[title_key],
            "name": candidate_item[name_key]
        })

    def _get_search_facets(self, search_facets, result):
        if result['organization'] is not None:
            self._add_to_items_or_increment(search_facets['organization'],
                                            result['organization'], "name", "title")

        for resource in result['resources']:
            self._add_to_items_or_increment(search_facets['res_format'], resource, "format", "format")

        for group in result['groups']:
            self._add_to_items_or_increment(search_facets['groups'], group, "name", "name")

        return search_facets

    async def search(self, query={}):
        """Search packages (datasets) that match the query.

        Query can contain freetext search, drilldown on facets and can specify which facets to return

        This specific implemantation doesn't seperate searching, and constructing the resulting object.
        In the future these need to be seperated, and made pluggable.

        :param query:
        :return:

        """
        results = copy.deepcopy(self.all_packages)

        # filter results for freetext query
        #   needs to be implemented

        # filter results for faceted search
        filtered_results = []
        for possible_result in results['result']['results']:
            if self._result_matches_facets(possible_result, query):
                filtered_results.append(possible_result)

        # update metadata
        results['result']['results'] = filtered_results
        results['result']['count'] = len(filtered_results)

        # update facets
        results['result']['facets'] = reduce(self._get_facets,
                                             filtered_results,
                                             self._get_empty_facets())
        results['result']['search_facets'] = reduce(self._get_search_facets,
                                                    filtered_results,
                                                    self._get_empty_search_facets())

        # filter facets based on requested facets
        if action_api.SearchParam.FACET_FIELDS in query:
            results['result']['facets'] = {k: v for k, v in results['result']['facets'].items()
                                           if k in query[action_api.SearchParam.FACET_FIELDS] }
            results['result']['search_facets'] = {k: v for k, v in results['result']['search_facets'].items()
                                                  if k in query[action_api.SearchParam.FACET_FIELDS] }

        # apply paging
        begin = query[action_api.SearchParam.START] if action_api.SearchParam.START in query else 0
        if action_api.SearchParam.ROWS in query:
            end = begin + query[action_api.SearchParam.ROWS]
            results['result']['results'] =  results['result']['results'][begin:end]
        else:
            results['result']['results'] = results['result']['results'][begin:]

        return results


async def is_healthy():
    return await implemented_search.is_healthy()


async def search(query={}):
    return await implemented_search.search(query)


implemented_search = InMemorySearch()
