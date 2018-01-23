import json
import pathlib
import pprint

attributes = {}
p = pathlib.Path('packages/')
for filename in p.glob('*.json'):
    with open(filename) as fh:
        p = json.load(fh)
        for a in p:
            if a == 'spatial':
                print(p[a])
            if a not in attributes:
                attributes[a] = 1
            else:
                attributes[a] = attributes[a] + 1

pprint.pprint(attributes)
