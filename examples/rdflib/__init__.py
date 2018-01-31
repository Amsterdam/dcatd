import os.path
import sys
from pprint import pprint

import rdflib
import json
import rdflib_jsonld as jsonld

IDENTIFIER = '9c3036b8-f6ac-4a4e-9036-5a3cc90c3900'
filename = os.path.dirname(__file__).join([IDENTIFIER + '.json'])
#pprint(filename)
with open(filename, mode='r') as f:
    ckan = json.load(f)

ckan.update({
    "@id": f'http://catalog.amsterdam.nl/{IDENTIFIER}',
    "@context": {
        "@vocab": "https://ckan.org/terms/"
    }
})
#pprint(ckan)
g = rdflib.Graph().parse(
    data=json.dumps(ckan), format='json-ld'
)
# for triple in g:
#     pprint(triple)

print(g.serialize(format="json-ld").decode())
