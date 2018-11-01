import typing as T

from aiopluggy import HookimplMarker
from pyld import jsonld

from datacatalog.dcat import Direction

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
def mds_canonicalize(data: dict, id: T.Optional[str]=None, direction: Direction=Direction.GET) -> dict:
    # language=rst
    """

    :param data:
    :param id: Can be one of three values:

        #.  ``None``: do nothing with the ``@id`` or ``dct:identifier`` fields.
        #.  ``""`` (the empty string): remove the ``@id`` or ``dct:identifier`` fields.
        #.  ``str`` (non-empty string): set the ``@id`` or ``dct:identifier`` fields.

    :param direction: direction of the
    """
    ctx = context()
    # The expansion is implicitly done in jsonld.compact() below.
    # data = jsonld.expand(data)
    retval = jsonld.compact(data, ctx)
    old_id = retval.get('@id')
    sort_modified = retval.get('ams:sort_modified', None)
    retval = DATASET.canonicalize(retval, direction=direction)
    if 'dcat:distribution' not in retval:
        retval['dcat:distribution'] = []
    retval['@context'] = ctx
    if direction == Direction.GET:
        if 'overheid:authority' not in retval:
            retval['overheid:authority'] = 'Amsterdam'

    for distribution in retval.get('dcat:distribution', []):
        if '@id' in distribution:
            del distribution['@id']
        if direction == Direction.PUT:
            if 'ams:distributionType' in distribution:
                if 'dct:format' in distribution and distribution['ams:distributionType'] != 'file':
                    del distribution['dct:format']
                if 'dct:byteSize' in distribution and distribution['ams:distributionType'] != 'file':
                    del distribution['dct:byteSize']
                if 'ams:serviceType' in distribution and distribution['ams:distributionType'] != 'api':
                    del distribution['ams:serviceType']
                if distribution['ams:distributionType'] == 'file' and (
                        not 'dct:format' in distribution or distribution['dct:format'] == ''):
                    distribution['dct:format'] = 'application/octet-stream'

        else:  # Direction.GET
            if 'dct:license' not in distribution and 'ams:license' in retval:  # Inherit license from dataset
                distribution['dct:license'] = retval['ams:license']

    if id == '':
        for item in ['@id', 'dct:identifier']:
            if item in retval:
                del retval[item]
    elif id is not None:
        retval['@id'] = f"ams-dcatd:{id}"
        retval['dct:identifier'] = str(id)
    elif old_id is not None:
        retval['@id'] = old_id
    if sort_modified is not None:
        retval['ams:sort_modified'] = sort_modified
    return retval


@_hookimpl
async def mds_json_schema(app) -> dict:
    result = DATASET.schema
    owners = await app.hooks.storage_extract(
        app=app, ptr='/properties/ams:owner', distinct=True)
    owners = sorted([owner async for owner in owners])
    result['properties']['ams:owner']['examples'] = owners

    keywords = await app.hooks.storage_extract(
        app=app, ptr='/properties/dcat:keyword/items', distinct=True)
    keywords = sorted([keyword async for keyword in keywords])
    result['properties']['dcat:keyword']['items']['examples'] = keywords
    return result


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
