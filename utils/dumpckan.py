import json
from urllib import request

with request.urlopen('https://api.data.amsterdam.nl/catalogus/api/3/action/package_list') as response:
    assert 200 == response.getcode()
    packagenames = json.load(response)['result']

for package in packagenames:
    with request.urlopen(f'https://api.data.amsterdam.nl/catalogus/api/3/action/package_show?id={package}') as result:
        assert 200 == result.getcode()
        with open(f'packages/{package}.json', mode='w') as fh:
            json.dump(json.load(result)['result'], fh, indent=2, sort_keys=True)
