from aiopluggy import HookimplMarker
from pyld import jsonld

from .constants import CONTEXT
from .dataset import DATASET

_hookimpl = HookimplMarker('datacatalog')

_SCHEMA = 'dcat-ap-ams'
_BASE_URL = 'http://localhost/'


@_hookimpl
def initialize_sync(app):
    global _BASE_URL
    _BASE_URL = app.config['web']['baseurl']


@_hookimpl
def mds_name():
    return _SCHEMA


@_hookimpl
def mds_canonicalize(data: dict) -> dict:
    expanded = jsonld.expand(data)
    retval = jsonld.compact(expanded, context())
    for distribution in retval['dcat:distribution']:
        if '@id' in distribution:
            del distribution['@id']
    return retval


@_hookimpl
def mds_json_schema() -> dict:
    return DATASET.schema


@_hookimpl
def mds_full_text_search_representation(data: dict) -> str:
    return DATASET.full_text_search_representation(data)


@_hookimpl
def mds_context() -> dict:
    return context()


def context(base_url=None) -> dict:
    if base_url is None:
        base_url = _BASE_URL
    retval = dict(CONTEXT)
    retval['ams-dcatd'] = base_url + 'datasets/'
    return retval


# print(json.dumps(
#     DATASET.schema,
#     indent='  ', sort_keys=True
# ))

# print(DATASET.full_text_search_representation({
#     'dct:title': 'my dct:title',
#     'dcat:distribution': [
#         {
#             'dct:description': "de omschrijving van één of andere **resource** met <b>markdown</b> opmaak.",\
#             'dct:license': "cc-by-nc-sa"
#         }
#     ]
# }))
