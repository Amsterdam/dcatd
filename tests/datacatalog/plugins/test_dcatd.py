import unittest
import datetime

from datacatalog.plugins.dcat_ap_ams import mds_canonicalize


class TestDcatd(unittest.TestCase):

    @unittest.skip
    def test_canonicalize(self):
        self.maxDiff = None
        data = {
            "@id": "ams-dcatd:_FlXXpXDa-Ro3Q",
            "dcat:description": "Lijsten en locaties van verschillende "
                                "zorgvoorzieningen voor ouderen in\nAmsterdam: "
                                "verpleeg- en verzorgingshuizen, zorg en hulp "
                                "bij dementie en\ndienstencentra voor ouderen",
            "dcat:identifier": "_FlXXpXDa-Ro3Q",
            "dcat:title": "Ouderen",
            "dcat:distribution": [
                {"dct:format": "application/json"},
                {"dct:format": "application/json"},
                {"dct:format": "text/html"}
            ],
            "dcat:keyword": [
                "dementie",
                "dienstencentra",
                "ouderen",
                "verpleeghuizen",
                "verzorgingshuizen"
            ]
        }

        expected = {
            'dcat:title': 'Ouderen',
            'dcat:description': 'Lijsten en locaties van verschillende '
                                'zorgvoorzieningen voor ouderen in\nAmsterdam: '
                                'verpleeg- en verzorgingshuizen, zorg en hulp '
                                'bij dementie en\ndienstencentra voor ouderen',
            'dct:distribution': [
                {'dct:format': 'application/json'},
                {'dct:format': 'application/json'},
                {'dct:format': 'text/html'}
            ],
            'dcat:keyword': ['dementie', 'dienstencentra', 'ouderen',
                             'verpleeghuizen', 'verzorgingshuizen'],
            'dcat:identifier': '_FlXXpXDa-Ro3Q',
            '@context': {
                'ams': 'http://datacatalogus.amsterdam.nl/term/',
                'ckan': 'https://ckan.org/terms/',
                'class': 'ams:class#',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'dcat': 'http://www.w3.org/ns/dcat#',
                'dct': 'http://purl.org/dc/terms/',
                'foaf': 'http://xmlns.com/foaf/0.1/',
                'lang1': 'http://id.loc.gov/vocabulary/iso639-1/',
                'lang2': 'http://id.loc.gov/vocabulary/iso639-2/',
                'org': 'ams:org#',
                'overheid': 'http://standaarden.overheid.nl/owms/terms/',
                'overheidds': 'http://standaarden.overheid.nl/owms/terms/ds#',
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'skos': 'http://www.w3.org/2004/02/skos/core#',
                'theme': 'ams:theme#',
                'time': 'http://www.w3.org/2006/time#',
                'vcard': 'http://www.w3.org/2006/vcard/ns#',
                'dcat:dataset': {'@container': '@list'},
                'dcat:distribution': {'@container': '@set'},
                'dcat:keyword': {'@container': '@set'},
                'dcat:landingpage': {'@type': '@id'},
                'dcat:theme': {'@container': '@set',
                               '@type': '@id'},
                'dct:issued': {'@type': 'xsd:date'},
                'dct:language': {'@type': '@id'},
                'dct:modified': {'@type': 'xsd:date'},
                'foaf:homepage': {'@type': '@id'},
                'foaf:mbox': {'@type': '@id'},
                'vcard:hasEmail': {'@type': '@id'},
                'vcard:hasURL': {'@type': '@id'},
                'vcard:hasLogo': {'@type': '@id'},
                'ams-dcatd': 'http://localhost/datasets/'},
            '@id': 'ams-dcatd:_FlXXpXDa-Ro3Q'}

        canonicalized = mds_canonicalize(data)
        self.assertDictEqual(canonicalized, expected)

    def test_canonicalize_modifieddate(self):
        this_date = datetime.date.today().strftime('%Y-%m-%d')
        past_date = '2006-12-13'
        data = {
            "@id": "ams-dcatd:_FlXXpXDa-Ro3Q",
            "dcat:identifier": "_FlXXpXDa-Ro3Q",
            "dcat:distribution": [
                {"dct:format": "application/json"},
                {"dct:format": "application/json"},
                {"dct:format": "text/html"}
            ],
            "foaf:isPrimaryTopicOf": {'dct:issued': past_date}
        }

        canonicalized = mds_canonicalize(data)

        self.assertIn('dct:modified', canonicalized["foaf:isPrimaryTopicOf"])
        self.assertEqual(canonicalized["foaf:isPrimaryTopicOf"]['dct:modified'], this_date)

        for distribution in data['dcat:distribution']:
            self.assertNotIn('dct:modified', distribution)

        for distribution in canonicalized['dcat:distribution']:
            self.assertIn('dct:modified', distribution)
            self.assertEqual(distribution['dct:modified'], this_date)

        for distribution in data['dcat:distribution']:
            distribution['dct:modified'] = past_date

        canonicalized = mds_canonicalize(data)

        for distribution in canonicalized['dcat:distribution']:
            self.assertEqual(distribution['dct:modified'], this_date)
