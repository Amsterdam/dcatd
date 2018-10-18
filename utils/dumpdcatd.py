import argparse
import json
import os
from urllib import request

from pyld import jsonld

from datacatalog.plugins import dcat_ap_ams

PACKAGE_DIR = 'dcatddata'
os.makedirs(PACKAGE_DIR, exist_ok=True)

_CONTEXT = dcat_ap_ams.context()
_HEADERS = {
    "accept": "application/json",
    "accept-charset": "utf-8",
    "user-agent": "Deliberately empty"
}


def dump_dcatd(api_root):
    req = _get_request_with_headers(f'{api_root}/datasets')

    with request.urlopen(req) as response:
        assert 200 == response.getcode()
        datasets = json.load(response)

    datasets = jsonld.compact(datasets, _CONTEXT)
    print(json.dumps(datasets, indent=2))

    for dataset_iterator in datasets['dcat:dataset']:
        req = _get_request_with_headers(dataset_iterator['@id'])
        with request.urlopen(req) as response:
            assert 200 == response.getcode()
            dataset = json.load(response)
        dataset = jsonld.compact(dataset, _CONTEXT)
        with open(f"{PACKAGE_DIR}/{dataset['dct:identifier']}.json", mode='w') as fh:
            json.dump(dataset, fh, indent=2, sort_keys=True)


def _get_request_with_headers(url):
    req = request.Request(url)
    for key, val in _HEADERS.items():
        req.add_header(key, val)
    return req


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump dcatd data catalog.')
    parser.add_argument(
        'baseurl',
        nargs=1,
        metavar='URL',
        help='baseurl of the dcatd api instance'
    )
    args = parser.parse_args()
    dump_dcatd(args.baseurl[0])
