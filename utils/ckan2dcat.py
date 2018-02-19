import json
import os
import subprocess
import re
from urllib.parse import urlparse
import pathlib

import jsonpointer
from pyld import jsonld

from datacatalog import terms
from datacatalog.plugins.dcat_ap_ams.context import CONTEXT

CKANDIR = 'ckandata'
DCATDIR = 'dcatdata'


_CONTEXT = CONTEXT


def pandoc(input_, from_, to):
    # TODO remove this line:
    return input_

    #print(f"input: {input_}")
    return subprocess.run(
        ['pandoc', '-f', from_, '-t', to],
        input=input_.encode(), stdout=subprocess.PIPE, check=True
    ).stdout.decode()


class FieldType(object):
    @staticmethod
    def validate(value):
        pass

    @staticmethod
    def fulltext(value):
        return None

    @staticmethod
    def from_ckan(value):
        result = value.strip()
        return None if result == '' else result


class Date(FieldType):
    @staticmethod
    def validate(value):
        assert re.fullmatch(r'\d{4}-\d{2}-\d{2}\+0100', value)

    @staticmethod
    def from_ckan(value):
        assert re.fullmatch(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?', value)
        return value[:10] + '+0100'


class Distribution(FieldType):
    pass


class Distributions(FieldType):
    pass


class FOAFPerson(FieldType):
    @staticmethod
    def validate(value):
        assert 'foaf:name' in value

    @staticmethod
    def fulltext(value):
        retval = ' '.join(value.values())
        return retval.replace('mailto:', '')

    @staticmethod
    def from_ckan(ckan):
        if 'publisher' not in ckan:
            return None
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


class Keywords(FieldType):
    @staticmethod
    def from_ckan(tags):
        retval = [tag['name'].strip() for tag in tags]
        return retval or None


class Language(FieldType):
    @staticmethod
    def validate(value):
        assert value in {
            'lang2:nl',
            'lang2:en'
        }


class License(FieldType):
    @staticmethod
    def validate(value):
        assert value in {
            'cc-by',
            'cc-by-nc-nd',
            'cc-nc',
            'cc-zero',
            'other-open',
            'other-prop'
        }

    @staticmethod
    def from_ckan(value):
        if value in {'cc-by', 'cc-nc', 'cc-zero', 'other-open'}:
            return value
        if value in {'cc_by-nc-nd'}:
            return 'cc-by-nc-nd'
        if value in {'cc_by'}:
            return 'cc-by'
        if value in {'niet-gespecificeerd', 'notspecified'}:
            return None
        if value in {'publiek'}:
            return 'cc-zero'
        raise AttributeError(f"Unknown license: {value}")


class Markdown(FieldType):
    def __init__(self, from_):
        self.from_ = from_

    @staticmethod
    def fulltext(value):
        return pandoc(value, 'markdown', 'plain')

    def from_ckan(self, value):
        return pandoc(value, self.from_, 'markdown')


class Organization(FieldType):
    @staticmethod
    def fulltext(value):
        # TODO: enrich with known organizational info.
        return value

    @staticmethod
    def from_ckan(value):
        id = f"org:{value['name']}"
        org = list(
            org for org in terms.TERMS['org'] if org['@id'] == id
        )
        return org[0]


class TemporalUnit(FieldType):
    @staticmethod
    def validate(value):
        assert value in {
            None,
            'realtime',
            'minute',
            'hour',
            'part-time',
            'day',
            'week',
            'month',
            'quarter',
            'year',
            'other'
        }

    @staticmethod
    def from_ckan(value: str):
        return {
            'Geen tijdseenheid': None,
            'Jaren': 'year',
            'Minuten': 'minute',
            'Dagen': 'day',
            'Kwartalen': 'quarter'
        }[value]


class SpatialUnit(FieldType):
    @staticmethod
    def validate(value):
        assert value in {
            None,
            'specifieke-geometrie',
            'land',
            'regio',
            'gemeente',
            'stadsdeel',
            'gebied',
            'wijk',
            'buurt',
            'bouwblok',
            'postcode-pp4',
            'postcode-pp5',
            'postcode-pp6',
            'anders'
        }

    @staticmethod
    def from_ckan(value: str):
        return {
            'Geen geografie': None,
            'Buurt': 'buurt',
            'Gemeente': 'gemeente',
            'Land': 'land',
            'Regio': 'regio',
            'Specifieke punten/vlakken/lijnen': 'specifieke-geometrie',
            'Stadsdeel': 'stadsdeel'
        }[value]


class TextLine(FieldType):
    def __init__(self, max_length=None):
        self.max_length = max_length

    def validate(self, value):
        if self.max_length is not None:
            assert self.max_length >= len(value)
        assert not re.search(r'[\r\n]', value)


class Theme(FieldType):
    @staticmethod
    def validate(value):
        validator = URLSegment().validate
        for theme in value:
            assert 6 < len(theme)
            validator(theme)

    @staticmethod
    def from_ckan(groups):
        retval = ['theme:' + g['name'] for g in groups]
        all_themes = set(
            theme['@id'] for theme in terms.TERMS['theme']
        )
        assert all(
            theme in all_themes
            for theme in retval
        )
        return retval or None


class URL(FieldType):
    @staticmethod
    def validate(urls):
        for url in urls:
            urlparse(url)

    @staticmethod
    def from_ckan(value):
        return [v for v in value.split(' ') if len(v) > 0]


class URLSegment(FieldType):
    @staticmethod
    def validate(text):
        assert isinstance(text, str), text
        assert re.fullmatch(
            r"(?:%[a-f0-9]{2}|[-\w:@!$&'()*+,;=.~])*",
            text, re.IGNORECASE
        ), text


class VCard(FieldType):
    @staticmethod
    def fulltext(value):
        retval = ' '.join(value.values())
        return retval.replace('mailto:', '')


class VCardContact(VCard):
    @staticmethod
    def from_ckan(ckan):
        if 'contact_name' not in ckan:
            return None
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


class VCardOwner(VCard):
    @staticmethod
    def from_ckan(org):
        retval = {
            '@id': f"org:{org['name']}",
            'vcard:fn': org['title'].strip(),
            'vcard:note': pandoc(org['description'].strip(), 'html', 'rst'),
            'vcard:hasLogo': org['image_url'].strip()
        }
        email = org.get('publisher_email', '').strip()
        if email != '':
            retval['vcard:hasEmail'] = f"mailto:{email}"
        uri = org.get('publisher_uri', '').strip()
        if uri != '':
            retval['vcard:hasURL'] = uri
        return retval


class VCardPublisher(VCard):
    @staticmethod
    def from_ckan(ckan):
        if 'publisher' not in ckan:
            return None
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


_SCHEMA = {
    'ams:owner': {
        'type': Organization(),
        'ckan': '/organization'
    },
    'ams:publisher': {
        'type': VCardPublisher(),
        'ckan': None
    },
    'ams:spatial_description': {
        'type': TextLine(),
        'ckan': '/spatial'
    },
    'ams:spatial_unit': {
        'type': SpatialUnit(),
        'ckan': '/gebiedseenheid'
    },
    'ams:temporal_unit': {
        'type': TemporalUnit(),
        'ckan': '/tijdseenheid'
    },
    'dcat:contactPoint': {
        'type': VCardContact(),
        'ckan': None
    },
    'dcat:keyword': {
        'type': Keywords(),
        'ckan': '/tags'
    },
    'dcat:landingpage': {
        'type': URL(),
        'ckan': '/url'
    },
    'dcat:theme': {
        'type': Theme(),
        'ckan': '/groups'
    },
    'dct:description': {
        'type': Markdown('html'),
        'ckan': '/notes'
    },
    'dct:identifier': {
        'type': TextLine(),
        'ckan': '/id'
    },
    'dct:issued': {
        'type': Date(),
        'ckan': '/metadata_created'
    },
    'dct:license': {
        'type': License(),
        'ckan': '/license_id'
    },
    'dct:modified': {
        'type': Date(),
        'ckan': '/metadata_modified'
    },
    'dct:publisher': {
        'type': FOAFPerson(),
        'ckan': None
    },
    'dct:temporal': {
        'type': TextLine(),
        'ckan': '/temporal'
    },
    'dct:title': {
        'type': TextLine(),
        'ckan': '/title'
    }
}
_SCHEMA_KEYS = {
    v['ckan'][1:] for v in _SCHEMA.values() if v['ckan'] is not None
}.union({
    'publisher', 'publisher_email', 'publisher_uri'
}).union({
    'contact_name', 'contact_email', 'contact_uri'
})


def load_packages():
    retval = []
    for filename in pathlib.Path(CKANDIR).glob('*.json'):
        with open(filename) as fh:
            retval.append(json.load(fh))
    return retval


def dump_datasets(datasets):
    os.makedirs(DCATDIR, exist_ok=True)
    for dataset in datasets:
        try:
            expanded = jsonld.expand(dataset)
            compacted = jsonld.compact(expanded, _CONTEXT)
        except:
            print(json.dumps(dataset, indent=2, sort_keys=True))
            raise
        with open(f"{DCATDIR}/{compacted['ckan:name']}.json", 'w') as fh:
            json.dump(compacted, fh, indent=2, sort_keys=True)


def ckan2dcat_distribution(resources):
    retval = []
    for resource in resources:
        pass
    return retval


def ckan2dcat(ckan):
    retval = {
        '@context': dict(_CONTEXT),
        'dct:language': 'lang2:nl',
        'ams:class': 'class:open'
    }
    retval['@context']['@vocab'] = 'https://ckan.org/terms/'
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
        if data is None:
            continue
        data = field['type'].from_ckan(data)
        if data is not None:
            try:
                field['type'].validate(data)
            except:
                print(repr(data))
                raise
            retval[fieldname] = data
    # for k, v in ckan.items():
    #     if k not in _SCHEMA_KEYS:
    #         retval[k] = v
    retval['dcat:distribution'] = ckan2dcat_distribution(ckan['resources'])
    retval['@id'] = f"ams-dcatd:{retval['dct:identifier']}"
    retval['ckan:name'] = ckan['name']
    return retval


if __name__ == '__main__':
    dump_datasets(ckan2dcat(x) for x in load_packages())
