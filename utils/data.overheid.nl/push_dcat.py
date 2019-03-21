import json
import os
import re
import urllib
from urllib import request
from urllib.error import HTTPError
import pprint


filetype_prefix = 'http://publications.europa.eu/resource/authority/file-type/'

MAP_MEDIATYPE_FORMAT = {
    'text/csv': filetype_prefix + 'CSV',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': filetype_prefix + 'DOCX',
    'application/vnd.geo+json': filetype_prefix + 'JSON',
    'application/gml+xml': filetype_prefix + 'GML',
    'text/html': filetype_prefix + 'HTML',
    'application/json': filetype_prefix + 'JSON',
    'application/pdf': filetype_prefix + 'PDF',
    'image/png': filetype_prefix + 'PNG',
    'application/x-zipped-shp': filetype_prefix + 'SHP',
    'application/vnd.ms-excel': filetype_prefix + 'XLS',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': filetype_prefix + 'XLSX',
    'application/xml': filetype_prefix + 'XML',
    'application/octet-stream': filetype_prefix + 'TAR_XZ',  # How to represent Anders. Format is a required value
}

MAP_LANGUAGE = {
    'lang1:nl': 'http://publications.europa.eu/resource/authority/language/NLD',
}

# Map to value in https://waardelijsten.dcat-ap-donl.nl/overheid_license.json
MAP_LICENSES = {
    'cc-by': 'http://creativecommons.org/licenses/by/4.0/deed.nl',
    'cc-by-nc': 'http://creativecommons.org/licenses/by/4.0/deed.nl',  # ? cc-by-nc missing
    'cc-by-nc-nd': 'http://creativecommons.org/licenses/by/4.0/deed.nl',  # ? cc-by-nc-nd missing
    'cc-by-nc-sa': 'http://creativecommons.org/licenses/by-sa/4.0/deed.nl',  # ? cc-by-nc-nd missing
    'cc-by-nd': 'http://creativecommons.org/licenses/by/4.0/deed.nl',  # ? cc-by-nd missing
    'cc-by-sa': 'http://creativecommons.org/licenses/by-sa/4.0/deed.nl',
    'cc-nc': 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl',  # ? cc-nc missing
    'cc-zero': 'http://creativecommons.org/publicdomain/zero/1.0/deed.nl',
    'other-open': 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl',  # ? other-open missing
    'other-by': 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl',  # ? other-by missing
    'other-nc': 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl',  # ? other-nc missing
    'other-not-open': 'http://standaarden.overheid.nl/owms/terms/geslotenlicentie',
    'unspec': 'http://standaarden.overheid.nl/owms/terms/licentieonbekend',
}

# Map to https://waardelijsten.dcat-ap-donl.nl/overheid_frequency.json
MAP_FREQUENCY = {
    'unknown': 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',
    'realtime': 'http://publications.europa.eu/resource/authority/frequency/CONT',
    'day': 'http://publications.europa.eu/resource/authority/frequency/DAILY',
    '2pweek': 'http://publications.europa.eu/resource/authority/frequency/WEEKLY_2',
    'week': 'http://publications.europa.eu/resource/authority/frequency/WEEKLY',
    '2weeks': 'http://publications.europa.eu/resource/authority/frequency/WEEKLY_2',
    'month': 'http://publications.europa.eu/resource/authority/frequency/MONTHLY',
    'quarter': 'http://publications.europa.eu/resource/authority/frequency/QUARTERLY',
    '2pyear': 'http://publications.europa.eu/resource/authority/frequency/ANNUAL_2',
    'year': 'http://publications.europa.eu/resource/authority/frequency/ANNUAL',
    '2years': 'http://publications.europa.eu/resource/authority/frequency/BIENNIAL',
    '4years': 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',  # ? does not exist
    '5years': 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',
    '10years': 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',
    'reg': 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',  # ? does not exist
    'irreg': 'http://publications.europa.eu/resource/authority/frequency/IRREG',
    'req': 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',  # ? does not exist
    'other': 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN'
}

# Map themes to : https://standaarden.overheid.nl/owms/terms/TaxonomieBeleidsagenda.xml
MAP_THEMES = {
    'theme:none': 'http://standaarden.overheid.nl/owms/terms/Overige_economische_sectoren',  # ???
    'theme:bestuur-en-organisatie': 'http://standaarden.overheid.nl/owms/terms/Bestuur',
    'theme:bevolking': 'http://standaarden.overheid.nl/owms/terms/Sociale_zekerheid',
    'theme:dienstverlening': 'http://standaarden.overheid.nl/owms/terms/Economie',
    'theme:economie-haven': 'http://standaarden.overheid.nl/owms/terms/Economie',
    'theme:educatie-jeugd-diversiteit': 'http://standaarden.overheid.nl/owms/terms/Onderwijs_en_wetenschap',
    'theme:energie': 'http://standaarden.overheid.nl/owms/terms/Energie',
    'theme:geografie': 'http://standaarden.overheid.nl/owms/terms/Ruimte_en_infrastructuur',
    'theme:milieu-water': 'http://standaarden.overheid.nl/owms/terms/Natuur_en_milieu',
    'theme:openbare-orde-veiligheid': 'http://standaarden.overheid.nl/owms/terms/Openbare_orde_en_veiligheid',
    'theme:openbare-ruimte-groen': 'http://standaarden.overheid.nl/owms/terms/Natuur-_en_landschapsbeheer',
    'theme:sport-recreatie': 'http://standaarden.overheid.nl/owms/terms/Cultuur_en_recreatie',
    'theme:stedelijke-ontwikkeling': 'http://standaarden.overheid.nl/owms/terms/Ruimte_en_infrastructuur',
    'theme:toerisme-cultuur': 'http://standaarden.overheid.nl/owms/terms/Toerisme',
    'theme:verkeer-infrastructuur': 'http://standaarden.overheid.nl/owms/terms/Verkeer_(thema)',
    'theme:verkiezingen': 'http://standaarden.overheid.nl/owms/terms/Bestuur',
    'theme:werk-inkomen': 'http://standaarden.overheid.nl/owms/terms/Werk_(thema)',
    'theme:wonen-leefomgeving': 'http://standaarden.overheid.nl/owms/terms/Huisvesting_(thema)',
    'theme:zorg-welzijn': 'http://standaarden.overheid.nl/owms/terms/Zorg_en_gezondheid'
}


IDENTIFIER_PREFIX = "https://api.data.amsterdam.nl/dcatd/dataset"


def _request_with_headers(url, data=None, method=None, authorization=None):
    headers = {
        "accept": "application/json",
        "accept-charset": "utf-8",
        "user-agent": "Deliberately empty"
    }
    if authorization:
        headers['Authorization'] = authorization
    req = request.Request(url, data=data, method=method)
    for key, val in headers.items():
        req.add_header(key, val)
    return req


def dictionary_vary(a: dict, b: dict, exclude: dict, parent_key:str = None) -> bool:
    parent_exclude = exclude.get(parent_key, {})

    if set(a.keys()) - parent_exclude != set(b.keys()) - parent_exclude:
        return True

    for key, value in a.items():
        if key not in parent_exclude:
            if isinstance(value, dict):
                if not isinstance(b[key], dict) or dictionary_vary(value, b[key], exclude, key):
                    return True
            elif isinstance(value, list):
                if not isinstance(b[key],list) or len(value) != len(b[key]):
                    return True
                for i in range(len(value)):
                    if isinstance(value[i], dict):
                        if not isinstance(b[key][i], dict) or dictionary_vary(value[i], b[key][i], exclude, key):
                            return True
                    else: # We do not have lists of lists
                        if value[i] != b[key][i]:
                            return True
            elif key in ('modified', 'modification_date', 'issued'):
                if value[:8] != b[key][:8]:
                    return True
            else:
                if value != b[key]:
                    return True

    return False


def _convert_to_ckan(dcat):
    language = MAP_LANGUAGE[dcat['dct:language']]

    ckan = {
        'title': dcat['dct:title'],
        'notes': dcat['dct:description'],
        'dataset_status': f"http://data.overheid.nl/status/{dcat['ams:status']}",
        "owner_org": "gemeente-amsterdam",  # Should there be a relation between owner_org and owner ?
        # 'owner': dcat['ams:owner'],
        'resources': [
            {
                'title': dist['dct:title'],
                'description': dist['description'] if 'description' in dist else 'unknown',
                'url': dist['dcat:accessURL'],
                # 'resourceType': dist['ams:resourceType'],
                # 'distributionType': dist['ams:distributionType'],
                'mimetype':dist.get('dcat:mediaType', 'application/octet-stream'),  # ? default application/octet-stream if no dcat:mediaType
                'format': MAP_MEDIATYPE_FORMAT[dist.get('dcat:mediaType','application/octet-stream')],
                'name': dist['dc:identifier'],
                # 'classification':'public', # We only have public datasets in dcat ?
                'size': dist['dcat:byteSize'] if 'dcat:byteSize' in dist else None,
                'modification_date': dist['dct:modified'] if 'dct:modified' in dist else dist['foaf:isPrimaryTopicOf'][
                    'dct:modified'],
                'language': [language],  # Inherit from dataset
                'metadata_language': language,  # Inherit from dataset
                # 'metadata_created': dist['foaf:isPrimaryTopicOf']['dct:issued'],
                # 'metadata_modified': dist['foaf:isPrimaryTopicOf']['dct:modified'],
                'license_id': MAP_LICENSES[dist['dct:license']],
                # 'purl': dist['ams:purl']
            } for dist in dcat['dcat:distribution']
        ],

        'metadata_language': language,
        # 'metadata_created': dcat['foaf:isPrimaryTopicOf']['dct:issued'],
        # 'metadata_modified': dcat['foaf:isPrimaryTopicOf']['dct:modified'],
        'issued' : dcat['foaf:isPrimaryTopicOf']['dct:issued'],
        'modified': dcat['dct:modified'] if 'dct:modified' in dcat else dcat['foaf:isPrimaryTopicOf']['dct:modified'],
        'frequency': MAP_FREQUENCY.get(dcat['dct:accrualPeriodicity'],
                                       'http://publications.europa.eu/resource/authority/frequency/UNKNOWN'),
        # 'temporalUnit': "na",
        'language': [language],
        'contact_point_name': dcat['dcat:contactPoint']['vcard:fn'],
        'contact_point_email': dcat['dcat:contactPoint']['vcard:hasEmail'],
        # ? How to map publishers  to fixed list of organisations : https://waardelijsten.dcat-ap-donl.nl/donl_organization.json
        # 'publisher_email': dcat['dct:publisher']['foaf:mbox'],
        # 'publisher_name': dcat['dct:publisher']['foaf:name'],
        'publisher': 'http://standaarden.overheid.nl/owms/terms/Amsterdam',
        'theme': [ MAP_THEMES[theme] for theme in dcat['dcat:theme']],
        'tags': [ {"name": keyword} for keyword in dcat['dcat:keyword']],
        'license_id': MAP_LICENSES[dcat['ams:license']],
        'authority': "http://standaarden.overheid.nl/owms/terms/" + dcat['overheid:authority'][9:],
        'identifier': IDENTIFIER_PREFIX + dcat['dct:identifier'],
        'name': dcat['dct:identifier'].lower(),
        #'modifiedby': dcat['ams:modifiedby']
        }
    return ckan

def push_dcat():
    dcat_env = os.getenv('ENVIRONMENT', 'acc')  # acc or prod
    api_key = os.getenv('API_KEY')
    organisation_id = os.getenv('ORGANISATION_ID', 'gemeente-amsterdam')

    dcat_root = 'https://api.data.amsterdam.nl/dcatd' if dcat_env == 'prod' else 'https://acc.api.data.amsterdam.nl/dcatd'
    donl_root = 'https://data.overheid.nl/data' if dcat_env == 'prod' else 'http://beta-acc.data.overheid.nl/data'

    req = _request_with_headers(f'{dcat_root}/harvest')

    with request.urlopen(req) as response:
        assert 200 == response.getcode()
        datasets_new = json.load(response)
        datasets_new = datasets_new['dcat:dataset']

    # Get all old datasets for gemeente amsterdam
    req = _request_with_headers(f'{donl_root}/api/3/action/package_search?q=organization:gemeente-amsterdam')
    response = request.urlopen(req)
    assert response.code == 200
    response_dict0 = json.loads(response.read())
    assert response_dict0['success']
    datasets_old = response_dict0['result']['results']
    prefix_len = len(IDENTIFIER_PREFIX)
    identifier_index_map_old = {datasets_old[index]['identifier'][prefix_len:]: index for index in
                                range(len(datasets_old))}

    identifier_index_map_new = { IDENTIFIER_PREFIX + datasets_new[index]['dct:identifier']:index for index in range(len(datasets_new))}

    insert_count = 0
    update_count = 0
    delete_count = 0

    count = 0

    remove_resources = {}

    for ds_new in datasets_new:
        identifier = ds_new['dct:identifier']

        owner = ds_new['ams:owner']
        # Only import datasets where amsterdam is owner
        if not re.search('amsterdam', owner, flags=re.IGNORECASE):
            continue

        if not api_key:
            continue

        # if count > 10:
        #    break

        ds_new = _convert_to_ckan(ds_new)

        # check if dataset exists
        ds_old = datasets_old[identifier_index_map_old[identifier]] if identifier in identifier_index_map_old else None
        if ds_old:
            # Dataset already exists. Use package_update
            # First add ID's to ckan dataset
            id = ds_new['id'] = ds_old['id']

            name_id_map_old = { res_old['name']: res_old['id'] for res_old in ds_old['resources']}
            for res_new in ds_new['resources']:
                if res_new['name'] in name_id_map_old:
                    res_new['id'] = name_id_map_old[res_new['name']]
                # else A new id will be assigned

            name_set_new = { res_new['name'] for res_new in ds_new['resources']}

            # Check if old and new datasets are different
            exclude = {
                None: {
                    'author',
                    'author_email',
                    'basis_register',
                    'changetype',
                    'creator_user_id',
                    'groups',
                    'high_value',
                    'isopen',
                    'license_title',
                    'license_url',
                    'maintainer',
                    'maintainer_email',
                    'metadata_created',
                    'metadata_modified',
                    'national_coverage',
                    'num_resources',
                    'num_tags',
                    'organization',
                    'owner_org',
                    'private',
                    'referentie_data',
                    'revision_id',
                    'state',
                    'type',
                },
                'resources': {
                    'cache_last_updated',
                    'cache_url',
                    'created',
                    'datastore_active',
                    'last_modified',
                    'metadata_created'
                    'metadata_modified',
                    'mimetype_inner',
                    'package_id',
                    'position',
                    'resource_type',
                    'revision_id',
                    'size',
                    'state',
                    'url_type',
                    'webstore_last_updated',
                    'webstore_url',
                },
                'tags': {
                    'display_name',
                    'id',
                    'vocabulary_id',
                    'state',
                }
            }

            if not dictionary_vary(ds_new, ds_old, exclude):
                continue

            # Collect resources te be removed
            to_remove = []
            for i in reversed(range(len(ds_old['resources']))):
                if ds_old['resources'][i]['name'] not in name_set_new:
                    to_remove.append(ds_old['resources'][i]['id'])

            # Remove resource later
            remove_resources[id] = to_remove

            ds_new_string = urllib.parse.quote(json.dumps(ds_new))
            ds_new_string = ds_new_string.encode('utf-8')
            req.add_header('Content-Length', len(ds_new_string))

            req = _request_with_headers(f'{donl_root}/api/3/action/package_update?id={id}', data=ds_new_string, authorization=api_key, method='POST')
            try:
                response = request.urlopen(req)
            except HTTPError as err:
                if err.code == 409:
                    error_message = err.read()
                    print(error_message)
                    print("Problem with dataset : ")
                    pprint.pprint(ds_new)
                    continue
                else:
                    raise err

            assert response.code == 200
            response_dict2 = json.loads(response.read())
            if response_dict2['success']:
                update_count += 1

            updated_package = response_dict2['result']

            count += 1
            # pprint.pprint(updated_package)
        else:
            # Dataset does not exist . Use package_create
            ds_new_string = urllib.parse.quote(json.dumps(ds_new))
            ds_new_string = ds_new_string.encode('utf-8')
            req.add_header('Content-Length', len(ds_new_string))

            req = _request_with_headers(f'{donl_root}/api/3/action/package_create', data=ds_new_string, authorization=api_key, method='POST')
            try:
                response = request.urlopen(req)
            except HTTPError as err:
                if err.code == 409 or err.code == 400:
                    error_message = err.read()
                    print(error_message)
                    print("Problem with dataset : ")
                    pprint.pprint(ds_new)
                    continue
                else:
                    raise err

            assert response.code == 200
            response_dict3 = json.loads(response.read())
            if response_dict3['success']:
                insert_count += 1
            created_package = response_dict3['result']

            count += 1
            # pprint.pprint(created_package)

    # Delete datasets in datasets_old not in datasets_new
    for ds_old in datasets_old:
        if ds_old['identifier'] not in identifier_index_map_new:
            req = _request_with_headers(f'{donl_root}/api/3/action/package_delete?id={ds_old[id]}')
            response = request.urlopen(req)
            assert response.code == 200
            response_dict4 = json.loads(response.read())
            if response_dict4['success']:
                delete_count += 1

    # Delete resources
    delete_res_count = 0
    for ds_id, res_list in remove_resources:
        for res_id in res_list:
            req = _request_with_headers(f'{donl_root}/api/3/action/resource_delete?id={res_id}')
            response = request.urlopen(req)
            assert response.code == 200
            response_dict5 = json.loads(response.read())
            if response_dict5['success']:
                delete_res_count += 1

    print(f"Datasets inserted:, {insert_count}, Datasets updated: {update_count}, Datasets deleted: {delete_count}, Resources deleted: {delete_res_count}")


if __name__ == '__main__':
    push_dcat()

