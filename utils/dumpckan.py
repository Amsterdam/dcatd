import json
import os
from urllib import request

PACKAGE_DIR = 'ckandata'
os.makedirs(PACKAGE_DIR, exist_ok=True)

with request.urlopen('https://api.data.amsterdam.nl/catalogus/api/3/action/package_list') as response:
    assert 200 == response.getcode()
    packagenames = json.load(response)['result']

for package in packagenames:
    print(package)
    with request.urlopen(f'https://api.data.amsterdam.nl/catalogus/api/3/action/package_show?id={package}') as result:
        assert 200 == result.getcode()
        with open(f'{PACKAGE_DIR}/{package}.json', mode='w') as fh:
            json.dump(json.load(result)['result'], fh, indent=2, sort_keys=True)
