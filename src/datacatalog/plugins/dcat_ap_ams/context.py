from pyld import jsonld

CONTEXT = {
    'ams': 'http://datacatalogus.amsterdam.nl/',
    'ckan': 'https://ckan.org/terms/',
    'class': 'http://datacatalogus.amsterdam.nl/term/classification/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'lang2': 'http://id.loc.gov/vocabulary/iso639-1/',
    'org': 'http://datacatalogus.amsterdam.nl/term/organization/',
    # Volgens dcat-ap-nl '.../term', maar dat kan niet. Zucht...
    # Volgens allerlei andere overheidsdocumenten:
    'overheid': 'http://standaarden.overheid.nl/owms/terms/',
    # Zelf verzonnen; juiste waarde nog opzoeken [--PvB]
    'overheidds': 'http://standaarden.overheid.nl/owms/terms/ds#',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'skos': 'http://www.w3.org/2004/02/skos/core#',
    'theme': 'http://datacatalogus.amsterdam.nl/term/theme/',
    'time': 'http://www.w3.org/2006/time#',
    'vcard': 'http://www.w3.org/2006/vcard/ns#',
    'dcat:keyword': {'@container': '@set'},
    'dcat:landingpage': {'@type': '@id'},
    'dcat:theme': {'@container': '@set', '@type': '@id'},
    'dct:issued': {'@type': 'xsd:date'},
    'dct:language': {'@type': '@id'},
    'dct:modified': {'@type': 'xsd:date'},
    'foaf:homepage': {'@type': '@id'},
    'foaf:mbox': {'@type': '@id'},
    'vcard:hasEmail': {'@type': '@id'},
    'vcard:hasURL': {'@type': '@id'},
    'vcard:hasLogo': {'@type': '@id'}
}


def compact(data):
    expanded = jsonld.expand(data)
    return jsonld.compact(expanded, CONTEXT)
