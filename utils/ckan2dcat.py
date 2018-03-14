"""

NOTE on uploading existing data from CKAN to dcatd:

$ python dumpckan.py
$ python ckan2dcat.py https://api.data.amsterdam.nl/dcatd/
$ python resources2distributions.py [UPLOADURL] [JWT]
$ cd dcatdata
$ for d in *.json; do curl -XPOST --header "Authorization: Bearer [JWT]" [DCATDURL]/datasets -d @${d} & done

"""
import argparse
import json
import os
import subprocess
import re
from urllib.parse import urlparse
import pathlib

import jsonpointer
from pyld import jsonld

from datacatalog import terms
from datacatalog.plugins import dcat_ap_ams

CKANDIR = 'ckandata'
DCATDIR = 'dcatdata'


def pandoc(input_, from_, to):
    # TODO remove this line:
    #return input_

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
    def from_ckan(value):
        result = value.strip()
        return None if result == '' else result


class CatalogRecord(FieldType):
    @staticmethod
    def from_ckan(ckan):
        retval = {}
        for from_, to_ in {'metadata_created': 'dct:issued',
                           'metadata_modified': 'dct:modified'}.items():
            if from_ in ckan:
                assert re.fullmatch(
                    r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?',
                    ckan[from_]
                )
            retval[to_] = ckan[from_][:10] + '+0100'
        return retval


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
    @staticmethod
    def from_ckan(value):
        return []


class FOAFPerson(FieldType):
    @staticmethod
    def validate(value):
        assert 'foaf:name' in value

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
            'lang1:nl',
            'lang1:en'
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

    def from_ckan(self, value):
        return pandoc(value, self.from_, 'markdown')


class Organization(FieldType):
    @staticmethod
    def from_ckan(value):
        return value['title']


class AccrualPeriodicity(FieldType):
    @staticmethod
    def validate(value):
        assert value in {
            'unknown',
            'realtime',
            'day',
            '2pweek',
            'week',
            '2weeks',
            'month',
            'quarter',
            '2pyear',
            'year',
            '2years',
            '4years',
            '5years',
            '10years',
            'reg',
            'irreg',
            'req',
            'other'
        }

    @staticmethod
    def from_ckan(value):
        return {
            '': 'unknown',
            '4-jaarlijks': '4years',
            'Bij verkiezingen (vierjaarlijks)': '4years',
            'Geen vaste frequentie, alleen bij beleidswijzigingen vanuit het ministerie van I&W': 'irreg',
            'Halfjaarlijks': '2pyear',
            'Jaarlijks': 'year',
            'Minimaal 5 jaarlijks (cyclus europese richtlijn omgevingslawaai)': '5years',
            'Onregelmatig': 'irreg',
            'Regelmatig': 'reg',
            'Twee keer per week': '2pweek',
            'dagelijks': 'day',
            'een keer per 5 jaar': '5years',
            'jaarlijks': 'year',
            'kleinschalige topografie: jaarlijks, grootschalige topografie: maandelijks': 'month',
            'maandelijks': 'month',
            'om de 10 jaar': '10years',
            'onregelmatig': 'irreg',
            'op afroep': 'req',
            'wekelijks': 'week'
        }[value.strip()]


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
            'Maanden': 'month',
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


class Themes(FieldType):
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
    def validate(url):
        urlparse(url)


class URLSegment(FieldType):
    @staticmethod
    def validate(text):
        assert isinstance(text, str), text
        assert re.fullmatch(
            r"(?:%[a-f0-9]{2}|[-\w:@!$&'()*+,;=.~])*",
            text, re.IGNORECASE
        ), text


class VCard(FieldType):
    pass


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


# class VCardPublisher(VCard):
#     @staticmethod
#     def from_ckan(ckan):
#         if 'publisher' not in ckan:
#             return None
#         retval = {
#             'vcard:fn': ckan['publisher'].strip()
#         }
#         email = ckan.get('publisher_email', '').strip()
#         if email != '':
#             retval['vcard:hasEmail'] = f"mailto:{email}"
#         uri = ckan.get('publisher_uri', '').strip()
#         if uri != '':
#             retval['vcard:hasURL'] = uri
#         return retval


_SCHEMA = {
    'dct:title': {
        'type': TextLine(),
        'ckan': '/title'
    },
    'dct:description': {
        'type': Markdown('html'),
        'ckan': '/notes'
    },
    'dcat:distribution': {
        'type': Distributions(),
        'ckan': '/resources'
    },
    'dcat:landingPage': {
        'type': URL(),
        'ckan': '/url'
    },
    'dct:accrualPeriodicity': {
        'type': AccrualPeriodicity(),
        'ckan': '/frequency'
    },
    'dct:temporal': {
        'type': TextLine(),
        'ckan': '/temporal'
    },
    'ams:temporalUnit': {
        'type': TemporalUnit(),
        'ckan': '/tijdseenheid'
    },
    'ams:spatialDescription': {
        'type': TextLine(),
        'ckan': '/spatial'
    },
    'ams:spatialUnit': {
        'type': SpatialUnit(),
        'ckan': '/gebiedseenheid'
    },
    'ams:owner': {
        'type': Organization(),
        'ckan': '/organization'
    },
    'dcat:contactPoint': {
        'type': VCardContact(),
        'ckan': None
    },
    'dct:publisher': {
        'type': FOAFPerson(),
        'ckan': None
    },
    'dcat:theme': {
        'type': Themes(),
        'ckan': '/groups'
    },
    'dcat:keyword': {
        'type': Keywords(),
        'ckan': '/tags'
    },
    'ams:license': {
        'type': License(),
        'ckan': '/license_id'
    },
    'dct:identifier': {
        'type': TextLine(),
        'ckan': '/id'
    },
    'foaf:isPrimaryTopicOf': {
        'type': CatalogRecord(),
        'ckan': None
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


def dump_datasets(datasets, context):
    os.makedirs(DCATDIR, exist_ok=True)
    for dataset in datasets:
        try:
            expanded = jsonld.expand(dataset)
            compacted = jsonld.compact(expanded, context)
        except:
            print(json.dumps(dataset, indent=2, sort_keys=True))
            raise
        with open(f"{DCATDIR}/{compacted['ckan:name']}.json", 'w') as fh:
            json.dump(compacted, fh, indent=2, sort_keys=True)


dct_formats = {
    "xlsx": 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    "pdf": 'application/pdf',
    "csv": 'text/csv',
    "json": 'application/json',
    "geojson": 'application/vnd.geo+json',
    "shp": 'application/zip; format="shp"',
    "xml": 'application/xml'
}

resourcetypes = {
    'Data': 'data',
    'Documentatie': 'doc',
    'Weergave': 'vis',
    'Toepassingen': 'app'
}

distributiontypes = {
    'api': 'api',
    'file': 'file',
    'file.upload': 'file',
}

def ckan2dcat_distribution(resources):
    retval = []
    for resource in resources:
        ckan_format = (resource.get('format', None) or '').lower()
        dct_format = dct_formats.get(ckan_format, 'application/octet-stream')
        ams_disttype = distributiontypes.get(resource['resource_type'], 'file')
        retval.append(
            {
                'ams:classification': 'public',
                'ams:distributionType': ams_disttype,
                'ams:resourceType': resourcetypes[resource.get('type', 'Data')],
                'dcat:accessURL': resource['url'],
                'dcat:byteSize': resource['size'],
                'dct:title': resource['name'],
                'dct:description': resource['description'],
                'dct:format': dct_format,
                'foaf:isPrimaryTopicOf': {
                    'dct:issued': resource['created'],
                    'dct:modified': resource['last_modified']
                }
            }
        )
        if ams_disttype == 'api':
            servicetype = 'other'
            if ckan_format in ('wms', 'wfs'):
                servicetype = ckan_format
            retval[-1]['ams:serviceType'] = servicetype
    return retval


def ckan2dcat(ckan, context):
    context = dict(context)  # dict() because we mutate the context
    context['@vocab'] = 'https://ckan.org/terms/'
    retval = {
        '@context':context,
        'dct:language': 'lang1:nl'
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
        if data is None:
            continue
        try:
            data = field['type'].from_ckan(data)
        except AttributeError:
            print(data)
            raise
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
    retval['@id'] = f"ams-dcatd:{retval['dct:identifier']}"
    retval['ckan:name'] = ckan['name']
    return retval


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CKAN 2 DCAT.')
    parser.add_argument('baseurl', metavar='URL', help='baseurl of the dcatd instance')
    args = parser.parse_args()
    ctx = dcat_ap_ams.context(args.baseurl)
    dump_datasets((ckan2dcat(x, ctx) for x in load_packages()), ctx)
