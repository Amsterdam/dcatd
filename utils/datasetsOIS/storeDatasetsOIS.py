import copy
import datetime
import json
import re
import urllib

import jwt
import os
import random
import string
from time import time
from collections import defaultdict
from pprint import pprint
from urllib.parse import quote, urlparse, parse_qsl

import requests
from xlrd import open_workbook, xldate_as_tuple, XL_CELL_NUMBER
from datacatalog.plugins.dcat_ap_ams.constants import THEMES, ACCRUAL_PERIODICITY, TEMPORAL_UNIT, LANGUAGES, \
    SPACIAL_UNITS

DCAT_URL = os.getenv('DCAT_URL', "https://acc.api.data.amsterdam.nl/dcatd/")
DCAT_USER = os.getenv('DCAT_USER', 'citydata.acc@amsterdam.nl')
DCAT_PASSWORD = os.getenv('DCAT_PASSWORD', 'insecure')
OBJECTSTORE_ROOT = 'https://b98488fe31634db9955ebdff95db4f1e.objectstore.eu/ois/'

THEMES_MAP = {desc:label for (label, desc) in THEMES}
ACCRUAL_PERIODICITY_MAP = { desc: label for (label, desc) in ACCRUAL_PERIODICITY}
TEMPORAL_UNIT_MAP = { desc: label for (label, desc) in TEMPORAL_UNIT}
LANGUAGES_MAP = { desc: label for (label, desc) in LANGUAGES}
SPACIAL_UNITS_MAP = { desc: label for (label, desc) in SPACIAL_UNITS}

datemode = None


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
    result = True
    for resource in ds['dcat:distribution']:
        if not resource['dcat:accessURL'].startswith(OBJECTSTORE_ROOT):
            result = False
            break
    return result


def build_dataset(ds_row, datasets, tabellen, dataset_tabellen):
    ois_id = datasets['id'][ds_row]
    tags = []
    resources = []
    for tr in dataset_tabellen[str(ois_id)]:
        access_url = f"{OBJECTSTORE_ROOT}{quote(tabellen['bestandsnaam'][tr])}.{tabellen['bestandstype'][tr]}"
        # TODO: Verify existence of access_url
        dct_modified = get_excel_date(tabellen['datum gewijzigd'][tr])
        if not dct_modified:
            dct_modified = datetime.date.today().isoformat()

        resource = {
                'dct:title': tabellen['tabeltitel'][tr],
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
        'dct:title': datasets['naam'][ds_row],
        'dct:description': description,
        'ams:status': 'beschikbaar',
        'dcat:distribution': resources,
        'dcat:theme': THEMES_MAP[theme],
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
    jsonresponse = response.json()
    return jsonresponse


def add_dataset(dataset:dict) -> int:
    pass


def update_dataset(id1: str, dataset: dict, access_token: str) -> int:
    url = f"{DCAT_URL}/datasets/{id1}"
    response = requests.head(url)
    etag = response.headers['Etag']
    headers = copy.deepcopy(access_token)
    headers["If-Match"] = etag
    headers["Content-Type"] = 'application/json'
    body = urllib.parse.quote(json.dumps(dataset))
    body = body.encode('utf-8')
    response = requests.post( url, headers=headers, data=body)
    if response.status_code != 200:
        print(f"Request error: {response.e}")
    status = response.status_code


    pass


def delete_dataset(id1: str):
    pass


def datasets_equal(a: dict, b: dict):
    print(f"Comparing datasets {a['dct:identifier']},{b['dct:identifier']}")
    return True


_access_token = None


def get_access_token(username, password, acceptance=True):
    global _access_token

    if _access_token is not None:
        decoded = jwt.decode(_access_token, verify=False)
        # We should have more then 100 seconds left
        if int(time.time()) + 100 > int(decoded['exp']):
            _access_token = None

    if not _access_token:
        def randomword(length):
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for i in range(length))

        state = randomword(10)
        scopes = ['CAT/R','CAT/W']
        acc_prefix = 'acc.' if acceptance else ''
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
    file1 = '/Users/bart/tmp/dcat/meta.xlsx'
    data1 = read_ois_excelfile(file1)
    # pprint(data1)
    acceptance = re.search(r'acc', DCAT_URL)
    access_token = get_access_token(DCAT_USER, DCAT_PASSWORD, acceptance)
    if not access_token:
        print('Failed to login\n\n')
        os.exit(1)
    harvested = harvest_dcat_api(access_token)
    harvested_title = {ds['dct:title']:ds for ds in harvested['dcat:dataset']}
    data_title = {ds['dct:title']:ds for ds in data1}

    ds_add_count = 0
    ds_update_count = 0
    ds_delete_count = 0

    for ds_title, ds in data_title.items():
        if ds_title in harvested_title and not datasets_equal(ds, harvested_title[ds_title]):
            id1 = harvested_title[ds_title]['dct:identifier']
            update_dataset(id1, ds)
            ds_update_count += 1

        else:
            add_dataset(ds)
            ds_add_count += 1

    for ds_title, ds in harvested_title.items():
        if is_ois_dataset(ds) and ds_title not in data_title:
            id1 = harvested_title[ds_title]['dct:identifier']
            delete_dataset(id1)
            ds_delete_count += 1

    print(f'Datasets added: {ds_add_count}, updated: {ds_update_count}, deleted: {ds_delete_count}')

    # pprint(harvested)
