import copy
import datetime
import re

import jwt
import os
import random
import string
from time import time
import requests
from collections import defaultdict
from urllib.parse import quote, urlparse, parse_qsl

from xlrd import open_workbook, xldate_as_tuple, XL_CELL_NUMBER
from datacatalog.plugins.dcat_ap_ams.constants import THEMES, ACCRUAL_PERIODICITY, TEMPORAL_UNIT, LANGUAGES, \
    SPACIAL_UNITS
from utils.utils import dictionary_vary

# DCAT_URL = os.getenv('DCAT_URL', "https://acc.api.data.amsterdam.nl/dcatd/")
DCAT_URL = os.getenv('DCAT_URL', "http://localhost:8000/")

DCAT_USER = os.getenv('DCAT_USER', 'citydata.acc@amsterdam.nl')
DCAT_PASSWORD = os.getenv('DCAT_PASSWORD', 'insecure')
OIS_OBJECTSTORE_ROOT = 'https://b98488fe31634db9955ebdff95db4f1e.objectstore.eu/ois/'

THEMES_MAP = {desc:label for (label, desc) in THEMES}
ACCRUAL_PERIODICITY_MAP = { desc: label for (label, desc) in ACCRUAL_PERIODICITY}
TEMPORAL_UNIT_MAP = { desc: label for (label, desc) in TEMPORAL_UNIT}
LANGUAGES_MAP = { desc: label for (label, desc) in LANGUAGES}
SPACIAL_UNITS_MAP = { desc: label for (label, desc) in SPACIAL_UNITS}

datemode = None

DAY_IN_SECONDS = 24 * 60 * 60


def get_ois_excel_file(filename):
    tmpdir = os.getenv('TMPDIR', '/tmp')
    local_file = tmpdir + '/' + filename
    if not os.path.isfile(local_file) or time() - os.path.getmtime(local_file) > DAY_IN_SECONDS:
        url = OIS_OBJECTSTORE_ROOT + filename
        response = requests.get(url)
        response.raise_for_status()
        with open(local_file, 'wb') as file:
            file.write(response.content)
    return local_file


def get_excel_date(value: str):
    t = xldate_as_tuple(value, datemode)
    return datetime.date(t[0], t[1], t[2]).isoformat()


def read_ois_excelfile(file: str) -> dict:
    global datemode
    result = {}
    wb = open_workbook(file)
    datemode = wb.datemode
    col_title_map = {}
    for s in wb.sheets():
        result[s.name] = {
            'count' : s.nrows - 1
        }
        sheet = result[s.name]
        for row in range(s.nrows):
            for col in range(s.ncols):
                cell = s.cell(row, col)
                value = cell.value
                ctype = cell.ctype
                if ctype == XL_CELL_NUMBER and value == int(value):
                    value = int(value)
                str_col = str(col)
                if row == 0:
                    value = value.lower()
                    col_title_map[str_col] = value
                    sheet[value] = []
                else:
                    sheet[col_title_map[str_col]].append(value)

    # Assign resources to datasets
    tabellen_sheet = result['tabellen']
    dataset_tabellen = defaultdict(list)
    for tr in range(tabellen_sheet['count']):
        dataset_id = tabellen_sheet['dataset id'][tr]
        dataset_tabellen[str(dataset_id)].append(tr)

    # Convert to datasets
    datasets = []
    datasets_sheet = result['datasets']
    for ds_row in range(datasets_sheet['count']):
        dataset = build_dataset(ds_row, datasets_sheet, tabellen_sheet, dataset_tabellen)
        if dataset:
            datasets.append(dataset)

    return datasets


def is_ois_dataset(ds):
    '''
    A dataset is a OIS dataset if all resources are in the OIS object store
    '''
    result = True
    for resource in ds['dcat:distribution']:
        if not resource['dcat:accessURL'].startswith(OIS_OBJECTSTORE_ROOT):
            result = False
            break
    return result


def check_link(url: str) -> bool:
    response = requests.head(url)
    # if response.status_code != 200:
    #     print(f"Link error for {url}: {response.status_code}")
    return True if response else False


def canonicalize(value: str):
    return value.strip().replace('\r\n', '\n')


def build_dataset(ds_row, datasets, tabellen, dataset_tabellen):
    ois_id = datasets['id'][ds_row]
    tags = []
    resources = []
    for tr in dataset_tabellen[str(ois_id)]:
        access_url = f"{OIS_OBJECTSTORE_ROOT}{quote(tabellen['bestandsnaam'][tr])}.{tabellen['bestandstype'][tr]}"
        if not check_link(access_url):
            print(f"Dataset {datasets['naam'][ds_row]} contains invalid url {access_url}")
            continue

        dct_modified = get_excel_date(tabellen['datum gewijzigd'][tr])
        if not dct_modified:
            dct_modified = datetime.date.today().isoformat()

        resource = {
                'dct:title': canonicalize(tabellen['tabeltitel'][tr]),
                'dcat:accessURL': access_url,
                'ams:resourceType': 'data',
                'ams:distributionType': 'file',
                'dcat:mediaType': 'application/vnd.ms-excel',
                'ams:classification': 'public',
                'dct:license': 'cc-by',
                'dct:modified': dct_modified
            }
        resources.append(resource)

    if len(resources) == 0:
        return None

    theme = datasets['thema'][ds_row]

    if 'beschrijving' in datasets and datasets['beschrijving'][ds_row]:
        description = datasets['beschrijving'][ds_row]
    else:
        description = f"<p>Diverse datasets met statistieken van Onderzoek, Informatie en Statistiek.</p><p>Thema: {theme}"
        gebied = datasets['omschrijving gebied'][ds_row].strip()
        if gebied:
            description += f", <br/>Detailniveau: {gebied}</p>"

    if 'tags' in datasets and datasets['tags'][ds_row]:
        keywords = datasets['tags'][ds_row].split(',')
    else:
        keywords = []

    inhoudelijk_contactpersoon = datasets['inhoudelijk contactpersoon'][ds_row] \
        if 'inhoudelijk contactpersoon' in datasets else datasets['nhoudelijk contactpersoon'][ds_row]

    technisch_contactpersoon =  datasets['technisch contactpersoon'][ds_row]
    ds = {
        'dct:title': canonicalize(datasets['naam'][ds_row]),
        'dct:description': canonicalize(description),
        'ams:status': 'beschikbaar',
        'dcat:distribution': resources,
        'dcat:theme': [ THEMES_MAP[theme] ],
        'dcat:keyword': keywords,
        'ams:license': 'cc-by',
        'overheid:authority': 'overheid:Amsterdam',
        'dct:identifier': '',
        'dct:publisher': {
            'foaf:name': technisch_contactpersoon or 'OIS/Datapunt',
            'foaf:mbox': 'algemeen.OIS@amsterdam.nl'
        },
        'dct:accrualPeriodicity': ACCRUAL_PERIODICITY_MAP.get(datasets['wijzigingsfrequentie'][ds_row], 'unknown'),
        'ams:temporalUnit': TEMPORAL_UNIT_MAP.get(datasets['tijdseenheid'][ds_row], 'na'),
        'dct:language': LANGUAGES_MAP.get(datasets['taal'][ds_row], 'lang1:nl'),
        'ams:owner': datasets['eigenaar'][ds_row] or 'Gemeente Amsterdam, Onderzoek, Informatie en Statistiek',
        'dcat:contactPoint': {
            'vcard:fn': inhoudelijk_contactpersoon,
            'vcard:hasEmail': datasets['e-mail inhoudelijk contactpersoon'][ds_row]
        },
        'overheidds:doel': datasets['doel'][ds_row],
        "foaf:isPrimaryTopicOf": {
            "dct:issued": get_excel_date(datasets['publicatiedatum'][ds_row]),
            "dct:modified": datetime.date.today().isoformat()
        }
    }

    if datasets['tijdsperiode van'][ds_row] and datasets['tijdsperiode tot'][ds_row]:
        has_beginning = get_excel_date(datasets['tijdsperiode van'][ds_row])
        has_end = get_excel_date(datasets['tijdsperiode tot'][ds_row])
        if has_beginning and has_end:
            ds['dct:temporal'] = {
                'time:hasBeginning': has_beginning,
                'time:hasEnd': has_end
            }

    if datasets['meer informatie'][ds_row]:
        ds['dcat:landingPage'] = datasets['meer informatie'][ds_row]

    if datasets['omschrijving gebied'][ds_row]:
        ds['ams:spatialDescription'] = datasets['omschrijving gebied'][ds_row]

    if datasets['gebiedseenheid'][ds_row]:
        ds['ams:spatialUnit'] = SPACIAL_UNITS_MAP.get(datasets['gebiedseenheid'][ds_row], 'na')

    if datasets['coördinaten gebied'][ds_row]:
        ds['dct:spatial'] = datasets['coördinaten gebied'][ds_row]

    if datasets['juridische grondslag'][ds_row]:
        ds['overheid:grondslag'] = datasets['juridische grondslag'][ds_row]

    return ds


def harvest_dcat_api(access_token):
    url = f"{DCAT_URL}/harvest"
    response = requests.get(url, headers=access_token)
    if not response:
        print(f"Request error: {response.status_code}")
    jsonresponse = response.json()
    return jsonresponse


def add_dataset(dataset:dict, access_token: str) -> int:
    url = f"{DCAT_URL}/datasets"
    dataset.pop('dct:identifier', None)
    dataset.pop('@id', None)
    headers = copy.deepcopy(access_token)
    headers["Content-Type"] = 'application/json'
    response = requests.post(url, headers=headers, json=dataset)
    if not response:
        print(f"Request error: {response.status_code}")
    return 1 if response else 0


def update_dataset(id1: str, dataset: dict, access_token: str) -> int:
    url = f"{DCAT_URL}/datasets/{id1}"
    response = requests.get(url)
    etag = response.headers['Etag']
    headers = copy.deepcopy(access_token)
    headers["If-Match"] = etag
    headers["Content-Type"] = 'application/json'
    response = requests.put( url, headers=headers, json=dataset)
    if not response:
        print(f"Request error: {response.status_code}")
    return 1 if response else 0


def delete_dataset(id1: str, dataset: dict, access_token: str) -> int:
    dataset['ams:status'] = 'niet_beschikbaar'
    return update_dataset(id1, dataset, access_token)


def datasets_equal(new: dict, old: dict):
    # We do not want to modify the new datasets here
    new = copy.deepcopy(new)
    print(f"Comparing datasets {new['dct:identifier']},{old['dct:identifier']}")

    # Sort lists to have the same order in old and new
    new['dcat:keyword'] = sorted(new['dcat:keyword'])
    old['dcat:keyword'] = sorted(old['dcat:keyword'])
    new['dcat:theme'] = sorted(new['dcat:theme'])
    old['dcat:theme'] = sorted(old['dcat:theme'])
    new['dcat:distribution'] = sorted(new['dcat:distribution'], key=lambda res: res['dct:title'])
    old['dcat:distribution'] = sorted(old['dcat:distribution'], key=lambda res: res['dct:title'])

    exclude = {
        None: {
            'dct:identifier',
            '@id',
            'ams:modifiedby',
            'ams:sort_modified',
        },
        'dcat:distribution': {
            'dc:identifier',
            'dct:modified',
            '@id',
            'ams:purl',
            'foaf:isPrimaryTopicOf',
        },
        'foaf:isPrimaryTopicOf': {
            'dct:modified'
        }
    }

    is_different = dictionary_vary(new, old, exclude)
    return not is_different


_access_token = None


def get_access_token(username, password, environment1):
    if environment1 == 'localhost':
        return {}

    global _access_token

    if _access_token is not None:
        decoded = jwt.decode(_access_token, verify=False)
        # We should have more then 100 seconds left
        if int(time()) + 100 > int(decoded['exp']):
            _access_token = None

    if not _access_token:
        def randomword(length):
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for i in range(length))

        state = randomword(10)
        scopes = ['CAT/R','CAT/W']
        acc_prefix = 'acc.' if environment1 == 'acc' else ''
        authzUrl = f'https://{acc_prefix}api.data.amsterdam.nl/oauth2/authorize'
        params = {
            'idp_id': 'datapunt',
            'response_type': 'token',
            'client_id': 'citydata',
            'scope': ' '.join(scopes),
            'state': state,
            'redirect_uri' : f'https://{acc_prefix}data.amsterdam.nl/'
        }

        response = requests.get(authzUrl, params, allow_redirects=False)
        if response.status_code == 303:
            location = response.headers["Location"]
        else:
           return {}

        data = {
           'type':'employee_plus',
           'email': username,
           'password': password,
        }

        response = requests.post(location, data=data, allow_redirects=False)
        if response.status_code == 303:
            location = response.headers["Location"]
        else:
            return {}

        response = requests.get(location, allow_redirects=False)
        if response.status_code == 303:
            returned_url = response.headers["Location"]
        else:
            return {}

        # Get grantToken from parameter aselect_credentials in session URL
        parsed = urlparse(returned_url)
        fragment = parse_qsl(parsed.fragment)
        _access_token = fragment[0][1]

    return {"Authorization": 'Bearer ' + _access_token}


if __name__ == '__main__':

    excel_file = 'meta.xlsx'
    local_excel_file = get_ois_excel_file(excel_file)
    data1 = read_ois_excelfile(local_excel_file)
    if re.search(r'acc', DCAT_URL):
        environment1 = 'acc'
    elif re.search(r'localhost', DCAT_URL):
        environment1 = 'localhost'
    else:
        environment1 = 'prod'
    access_token = get_access_token(DCAT_USER, DCAT_PASSWORD, environment1)
    if not access_token and environment1 != 'localhost':
        print('Failed to login\n\n')
        os.exit(1)
    harvested_all = harvest_dcat_api(access_token)
    harvested = list(filter( lambda ds: ds['ams:status'] != 'niet_beschikbaar', harvested_all['dcat:dataset']))
    harvested_title = {ds['dct:title']:ds for ds in harvested}
    data_title = {ds['dct:title']:ds for ds in data1}

    to_add = []
    to_update = {}
    to_delete = {}

    for ds_title, ds in data_title.items():
        if ds_title in harvested_title:
            old_ds = harvested_title[ds_title]
            if not datasets_equal(ds, old_ds):
                # Update identifier for dataset
                id1 = harvested_title[ds_title]['dct:identifier']
                ds['dct:identifier'] = id1
                # Update identifiers for distribution
                old_identifiers = { res['dct:title']: res['dc:identifier'] for res in old_ds['dcat:distribution']}
                for res in ds['dcat:distribution']:
                    old_identifier = old_identifiers.get(res['dct:title'])
                    if old_identifier:
                        res['dc:identifier'] = old_identifier
                    else:
                        res.pop('dc:identifier', None)
                to_update[id1] = ds
            # else: No update required. Datasets equal
        else:
            to_add.append(ds)

    for ds_title, ds in harvested_title.items():
        if is_ois_dataset(ds) and ds_title not in data_title:
            id1 = harvested_title[ds_title]['dct:identifier']
            to_delete[id1] = ds

    print(f'To be added {len(to_add)}, to be updated: {len(to_update)}, To be deleted: {len(to_delete)}')
    total_len = len(to_add) + len(to_update) + len(to_delete)
    if total_len > 0:
        print('Proceed (yes or no) >')
        if input() != 'yes':
            print("Aborted")
            os.exit(0)
    ds_add_count = 0
    ds_update_count = 0
    ds_delete_count = 0

    for ds in to_add:
        ds_add_count += add_dataset(ds, access_token)

    for id1, ds in to_update.items():
        ds_update_count += update_dataset(id1, ds, access_token)

    for id1, ds in to_delete.items():
        ds_delete_count += delete_dataset(id1, ds, access_token)

    print(f'Datasets added: {ds_add_count}, updated: {ds_update_count}, deleted: {ds_delete_count}')
