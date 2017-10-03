# test fixtures

### Packages from [ckan demo](https://demo.ckan.org/)

- packages.json downloaded from:
https://demo.ckan.org/api/3/action/package_search?facet.field=%5B%22groups%22,%22res_format%22,%22organization%22%5D&fq=&rows=3&sort=name+asc&start=0
(mind the subset of 3 results in this url)
- individual {id}.json files downloaded from the ids in the previous result
https://demo.ckan.org/api/3/action/package_show?id=62513382-3b26-4bc8-9096-40b6ce8383c0

Python (3.6) example code:

```$python
import json
from urllib import request

DEMO_CATALOG_URL = "https://demo.ckan.org/api/3"

ALL_PACKAGES = f"{DEMO_CATALOG_URL}/action/package_search?facet.field=%5B%22groups%22,%22res_format%22,%22organization%22%5D&fq=&rows=3&sort=name+asc&start=0" #noqa
PACKAGE_URL = f"{DEMO_CATALOG_URL}/action/package_show?id="

request.urlretrieve(ALL_PACKAGES, "fixtures/packages.json")

with open("fixtures/packages.json") as json_data:
    d = json.load(json_data)
    for package in d['result']['results']:
        request.urlretrieve(
            f"{PACKAGE_URL}{package['id']}",
            f"data/{package['id']}.json")
```

### current fixtures in git

Data retrieved on October 2nd, 2017 and manually updated `facets` and `search_facets` 
in `packages.json` to resemble this subset of 3.
