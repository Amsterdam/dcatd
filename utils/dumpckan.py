import argparse
import json
import os
from urllib import request

PACKAGE_DIR = 'ckandata'
os.makedirs(PACKAGE_DIR, exist_ok=True)

headers = {
    "accept": "application/json",
    "accept-charset": "utf-8",
    "accept-encoding": "deflate",
    "user-agent": "Deliberately empty"
}


def dump_ckan(api_root):
    req = _get_request_with_headers(f'{api_root}/3/action/package_list')

    with request.urlopen(req) as response:
        assert 200 == response.getcode()
        packagenames = json.load(response)['result']

    for package in packagenames:
        print(package)
        req = _get_request_with_headers(f'{api_root}/3/action/package_show?id={package}')
        with request.urlopen(req) as result:
            assert 200 == result.getcode()
            with open(f'{PACKAGE_DIR}/{package}.json', mode='w') as fh:
                json.dump(json.load(result)['result'], fh, indent=2, sort_keys=True)


def _get_request_with_headers(url):
    req = request.Request(url)
    for key, val in headers.items():
        req.add_header(key, val)
    return req


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DUMP CKAN.')
    parser.add_argument(
        'baseurl',
        nargs=1,
        metavar='URL',
        help='baseurl of the ckan api instance'
    )
    args = parser.parse_args()
    dump_ckan(args.baseurl[0])
