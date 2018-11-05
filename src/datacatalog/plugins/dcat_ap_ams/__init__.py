from copy import deepcopy
import datetime
import logging
import typing as T

from aiopluggy import HookimplMarker
from pyld import jsonld

from .constants import CONTEXT
from .dataset import DATASET, DISTRIBUTION


_hookimpl = HookimplMarker('datacatalog')
_BASE_URL = 'http://localhost/'
_logger = logging.getLogger(__name__)


def _get_sort_modified(doc: dict) -> str:
    # language=rst
    """Sorteerdatum.

    Wordt aangeroepen door zowel :func:`mds_before_storage` als
    :func:`mds_after_storage`. Sorteren op, in onderstaande volgorde. Als veld
    niet gevuld is, dan volgende datum gebruiken:

    verversingsdatum resource: dct:modified
    wijzigingsdatum resource: primarytopicof: dct:modified
    publicatiedatum resource: primarytopicof: dct:issued
    Als een dataset meerdere resources heeft dan de laatste datum nemen.
    wijzigingsdatum dataset: dct:modified
    publicatiedatum dataset: dct:issued
    wijzigingsdatum dataset: primarytopicof: dct:modified
    publicatiedatum dataset: primarytopicof: dct:issued

    Zet als laatse de last_modified_date in
    dataset->primarytopicof->dct:modified als die niet groter is. Anders gebruik
    als last_modified dataset->primarytopicof->dct:modified

    Deze waarde wordt getoond in de Frontend. OP deze wijze id de sortering
    consistent met de weergave in de Frontend, ook als die waardes niet correct
    worden geupdate.

    TODO: Check gebruik en regels omtrent 'foaf:isPrimaryTopicOf']->'dct:modified' en hoe dit te gebruiken in FE

    :param doc: de dataset
    :returns: sorteerdatum

    """
    last_modified = ''
    if 'dcat:distribution' in doc:
        for resource in doc['dcat:distribution']:
            if 'dct:modified' in resource and resource['dct:modified'] > last_modified:
                last_modified = resource['dct:modified']
        if not last_modified:
            dct_issued_resource = ''
            for resource in doc['dcat:distribution']:
                if 'foaf:isPrimaryTopicOf' in resource:
                    primary = resource['foaf:isPrimaryTopicOf']
                    if 'dct:modified' in primary and primary['dct:modified'] > last_modified:
                        last_modified = primary['dct:modified']
                    if 'dct_issued' in primary and primary['dct:issued'] > dct_issued_resource:
                        dct_issued_resource = primary['dct:issued']
            if not last_modified:
                last_modified = dct_issued_resource
    if not last_modified:
        if 'dct:modified' in doc:
            last_modified = doc['dct:modified']
        elif 'dct:issued' in doc:
            last_modified = doc['dct:issued']
        elif 'foaf:isPrimaryTopicOf' in doc:
            primary = doc['foaf:isPrimaryTopicOf']
            if 'dct:modified' in primary:
                last_modified = primary['dct:modified']
            elif 'dct:issued' in primary:
                last_modified = primary['dct:issued']

    return last_modified


@_hookimpl
def initialize_sync(app):
    global _BASE_URL
    _BASE_URL = app.config['web']['baseurl']


def _distributions_vary(a: dict, b: dict) -> bool:
    vary = False
    for name, property in DISTRIBUTION.properties:
        if not property.read_only and a.get(name) != b.get(name):
            vary = True
    return vary


def _datasets_vary(a: dict, b:dict) -> bool:
    vary = False
    for name, property in DATASET.properties:
        if name == 'dcat:distribution':
            continue
        if not property.read_only and a.get(name) != b.get(name):
            vary = True
    return vary


@_hookimpl
def mds_before_storage(app, data, old_data=None) -> dict:
    retval = deepcopy(data)
    retval.pop('dct:identifier', None)
    distributions = retval.get('dcat:distribution', [])

    # Already done by canonicalize():
    # _add_dc_identifiers_to(distributions=distributions)

    # Set all the meta-metadata timestamps correctly:
    if old_data is not None:
        if _datasets_vary(retval, old_data):
            try:
                old_issued = old_data['foaf:isPrimaryTopicOf']['dct:issued']
            except KeyError:
                _logger.error("Geen dct:issued in dataset %s", data['dct:title'])
                old_issued = '1970-01-01'
            retval['foaf:isPrimaryTopicOf'] = {
                'dct:issued': old_issued,
                'dct:modified': datetime.date.today().isoformat()
            }
        else:
            try:
                retval['foaf:isPrimaryTopicOf'] = old_data['foaf:isPrimaryTopicOf']
            except KeyError:
                # TODO: nette logging van dit probleem
                pass
        old_distributions = {
            old_distribution['dc:identifier']: old_distribution
            for old_distribution in old_data.get('dcat:distribution', [])
        }
        for distribution in distributions:
            old_distribution = old_distributions.get(distribution['dc:identifier'])
            if old_distribution is None:
                distribution['foaf:isPrimaryTopicOf'] = {
                    'dct:issued': datetime.date.today().isoformat(),
                    'dct:modified': datetime.date.today().isoformat()
                }
            else:
                distribution['foaf:isPrimaryTopicOf'] = old_distribution.get(
                    'foaf:isPrimaryTopicOf',
                    {
                        'dct:issued': '1970-01-01',
                        'dct:modified': '1970-01-01'
                    }
                )
                if _distributions_vary(distribution, old_distribution):
                    distribution['foaf:isPrimaryTopicOf']['dct:modified'] = datetime.date.today().isoformat()
    else:
        retval['foaf:isPrimaryTopicOf'] = {
            'dct:issued': datetime.date.today().isoformat(),
            'dct:modified': datetime.date.today().isoformat()
        }
        for distribution in distributions:
            distribution['foaf:isPrimaryTopicOf'] = {
                'dct:issued': datetime.date.today().isoformat(),
                'dct:modified': datetime.date.today().isoformat()
            }

    # Add ams:sortModified:
    retval['ams:sortModified'] = _get_sort_modified(retval)
    return retval


@_hookimpl
def mds_after_storage(app, data, doc_id):
    retval = deepcopy(data)
    # The following is a temporary measure, for as long as not all the data
    # in the database has been converted.
    # TODO: Remove
    if 'ams:license' in retval:  # Inherit license from dataset
        license = retval['ams:license']
        for distribution in retval.get('dcat:distribution', []):
            if 'dct:license' not in distribution:
                distribution['dct:license'] = license

    if 'overheid:authority' not in retval:
        retval['overheid:authority'] = 'overheid:Amsterdam'

    # Add proper identifiers:
    retval['@id'] = f"ams-dcatd:{doc_id}"
    retval['dct:identifier'] = str(doc_id)

    # Add ams:sortModified:
    if 'ams:sortMdified' not in retval:
        retval['ams:sortModified'] = _get_sort_modified(retval)

    distributions = retval.get('dcat:distribution', [])
    # _add_dc_identifiers_to(distributions)  # Already done by canonicalize()
    for distribution in distributions:
        # persistent URL:
        accessURL = distribution.get('dcat:accessURL', None)
        if accessURL is not None:
            distribution['ams:purl'] = f'ams-dcatd:{doc_id}/purls/' + distribution['dc:identifier']
        # dcat:mediaType:
        if 'dct:format' in distribution:
            distribution['dcat:mediaType'] = distribution['dct:format']
    retval = DATASET.set_required_values(retval)
    return retval


def _add_dc_identifiers_to(distributions: T.List[dict]) -> T.List[dict]:
    retval = deepcopy(distributions)
    all_persistent_ids = set(
        str(distribution['dc:identifier'])
        for distribution in retval
        if 'dc:identifier' in distribution
    )
    persistent_id = 1
    for distribution in retval:
        # persistent id:
        if 'dc:identifier' not in distribution:
            while str(persistent_id) in all_persistent_ids:
                persistent_id += 1
            all_persistent_ids.add(str(persistent_id))
            distribution['dc:identifier'] = str(persistent_id)
    return retval


@_hookimpl
def mds_canonicalize(app, data: dict) -> dict:
    # language=rst
    """
    TODO: Documentation of this vital function.
    """
    ctx = mds_context()
    # if '@context' not in data:
    #     _logger.warning("No @context in data to be canonicalized.")
    #     data['@context'] = ctx
    # The expansion is implicitly done in jsonld.compact() below.
    # data = jsonld.expand(data)
    retval = jsonld.compact(data, ctx)
    retval = DATASET.canonicalize(retval)
    if 'dcat:distribution' not in retval:
        retval['dcat:distribution'] = []
    retval['dcat:distribution'] = _add_dc_identifiers_to(retval['dcat:distribution'])
    retval['@context'] = ctx
    for distribution in retval['dcat:distribution']:
        if 'ams:distributionType' in distribution:
            if distribution['ams:distributionType'] != 'file':
                distribution.pop('dct:format')
            if distribution['ams:distributionType'] != 'file':
                distribution.pop('dct:byteSize')
            if distribution['ams:distributionType'] != 'api':
                distribution.pop('ams:serviceType')

    return retval


@_hookimpl
async def mds_json_schema(app, method: str) -> dict:
    result = DATASET.schema(method)
    if method == 'GET':
        return result
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
    retval = dict(CONTEXT)
    retval['ams-dcatd'] = _BASE_URL + 'datasets/'
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
