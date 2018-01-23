import json
import sys

import aiopluggy
import jsonpointer
from pyld import jsonld

hook = aiopluggy.HookimplMarker('datacatalog')


@hook
def schema_get():
    return _SCHEMA


@hook
def schema_types():
    pass


_CONTEXT = {
    'ams': 'http://amsterdam.nl/dcat-ap-ams/',
    'ckan': 'https://ckan.org/terms/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'org': 'http://amsterdam.nl/dcat-ap-ams/organizations/',
    'overheid': 'http://standaarden.overheid.nl/owms/term',
    # Zelf verzonnen; juiste waarde nog opzoeken [--PvB]
    'overheidds': 'http://standaarden.overheid.nl/owms/term/ds',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'skos': 'http://www.w3.org/2004/02/skos/core#',
    'theme': 'http://amsterdam.nl/dcat-ap-ams/themes/',
    'vcard': 'http://www.w3.org/2006/vcard/ns#',
    'dcat:keyword': {'@container': '@set'},
    'dcat:landingpage': {'@type': '@id'},
    'dcat:theme': {'@container': '@set', '@type': '@id'},
    'dct:language': {'@type': '@id'},
    'foaf:homepage': {'@type': '@id'},
    'foaf:mbox': {'@type': '@id'},
    'vcard:hasEmail': {'@type': '@id'},
    'vcard:hasURL': {'@type': '@id'},
    'vcard:hasLogo': {'@type': '@id'}
}


class FieldType(object):
    pass


class TextLine(FieldType):
    def __init__(self, max_length=None):
        self.max_length = max_length


class ReStructeredText(FieldType):
    pass


class URL(FieldType):
    pass


class VCard(FieldType):
    pass


class Tags(FieldType):
    pass


class Language(FieldType):
    pass


class FOAFPerson(FieldType):
    pass


class Organization(FieldType):
    pass


def _ckancontact2vcard(ckan):
    retval = {
        'vcard:fn': ckan['contact_name'].strip()
    }
    email = ckan.get('contact_email', '').strip()
    if email != '':
        retval['vcard:hasEmail'] = f"mailto:{email}"
    uri = ckan.get('contact_uri', '').strip()
    if uri != '':
        retval['vcard:hasURL'] = uri
    return retval


def _ckanorganization2vcard(org):
    retval = {
        '@id': f"org:{org['name']}",
        'vcard:fn': org['title'].strip(),
        'vcard:note': org['description'].strip(),
        'vcard:hasLogo': org['image_url'].strip()
    }
    email = org.get('publisher_email', '').strip()
    if email != '':
        retval['vcard:hasEmail'] = f"mailto:{email}"
    uri = org.get('publisher_uri', '').strip()
    if uri != '':
        retval['vcard:hasURL'] = uri
    return retval


def _ckanpublisher2vcard(ckan):
    retval = {
        'vcard:fn': ckan['publisher'].strip()
    }
    email = ckan.get('publisher_email', '').strip()
    if email != '':
        retval['vcard:hasEmail'] = f"mailto:{email}"
    uri = ckan.get('publisher_uri', '').strip()
    if uri != '':
        retval['vcard:hasURL'] = uri
    return retval


def _ckanpublisher2foaf(ckan):
    retval = {
        'foaf:name': ckan['publisher'].strip()
    }
    email = ckan.get('publisher_email', '').strip()
    if email != '':
        retval['foaf:mbox'] = f"mailto:{email}"
    uri = ckan.get('publisher_uri', '').strip()
    if uri != '':
        retval['foaf:homepage'] = uri
    return retval


_SCHEMA = {
    'ams:owner': {
        'type': VCard(),
        'ckan': '/organization',
        'convert': _ckanorganization2vcard
    },
    'ams:spatial_description': {
        'type': TextLine(),
        'ckan': '/spatial'
    },
    'ams:temporal_unit': {
        'type': TextLine(),
        'ckan': '/temporal'
    },
    'ams:publisher': {
        'type': VCard(),
        'ckan': None,
        'convert': _ckanpublisher2vcard
    },
    'ckan:frequency': {
        'type': TextLine(),
        'ckan': '/frequency'
    },
    'dcat:contactPoint': {
        'type': VCard(),
        'ckan': None,
        'convert': _ckancontact2vcard
    },
    'dcat:keyword': {
        'type': Tags(),
        'ckan': '/tags',
        'convert': lambda tags: [tag['name'].strip() for tag in tags]
    },
    'dcat:landingpage': {
        'type': URL(),
        'ckan': '/url'
    },
    'dcat:theme': {
        'type': URL(),
        'ckan': '/groups',
        'convert': lambda groups: [f"theme:{g['name']}" for g in groups]
    },
    'dct:description': {
        'type': ReStructeredText(),
        'ckan': '/notes'
    },
    'dct:identifier': {
        'type': TextLine(),
        'ckan': '/id'
    },
    'dct:publisher': {
        'type': FOAFPerson(),
        'ckan': None,
        'convert': _ckanpublisher2foaf
    },
    'dct:title': {
        'type': TextLine(),
        'ckan': '/title'
    },
}


def ckan2dcat(ckan):
    retval = {
        '@context': _CONTEXT,
        'dct:language': 'http://id.loc.gov/vocabulary/iso639-1/nl'
    }
    for fieldname, field in _SCHEMA.items():
        if 'ckan' not in field:
            continue
        if field['ckan'] is None:
            data = ckan
        else:
            try:
                data = jsonpointer.resolve_pointer(ckan, field['ckan'])
            except jsonpointer.JsonPointerException:
                continue
            #jsonpointer.set_pointer(ckan, field['ckan'], None)
        if 'convert' in field:
            retval[fieldname] = field['convert'](data)
        elif isinstance(data, str):
            retval[fieldname] = data.strip()
        else:
            continue
    retval['@id'] = f"http://amsterdam.nl/dcat/{retval['dct:identifier']}"
    #json.dump(ckan, sys.__stderr__, indent=2, sort_keys=True)
    return jsonld.compact(jsonld.expand(retval), _CONTEXT)


if __name__ == '__main__':
    with open('package.json') as fh:
        ckan = json.load(fh)
    json.dump(ckan2dcat(ckan), sys.__stdout__, indent=2, sort_keys=True)
