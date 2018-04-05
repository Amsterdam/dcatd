from . import constants
from .fieldtypes import *
from .distribution import DISTRIBUTION
from .logger import logger


def _ckan_2_dcat_theme_mapper(data):
    retval = 'theme:' + data['name']
    if retval not in {x[0] for x in constants.THEMES}:
        logger.warning("Unknown theme: '%s'", retval)
        return None
    return retval


DATASET = Object(json_pointer='').add(
    'dct:title',
    PlainTextLine(
        title="Titel",
        # description="Geef een titel van de gegevensset.",
        required=True,
        json_pointer='/title'
    )
).add(
    'dct:description',
    Markdown(
        title="Beschrijving",
        description="Geef een samenvatting van de inhoud van de gegevensset, welke gegevens zitten erin en wat is expliciet eruit gelaten",
        required=True,
        json_pointer='/notes',
        from_='html'
    )
).add(
    'dcat:distribution',
    List(
        DISTRIBUTION,
        title="Resources",
        json_pointer='/resources'
    )
).add(
    'overheidds:doel',
    Markdown(
        title="Doel",
        description="Geef aan met welk doel deze gegevensset is aangelegd. Waarom bestaat deze gegevensset?",
        json_pointer='/foobar'
    )
).add(
    'dcat:landingPage',
    String(
        title="URL voor meer informatie",
        format='uri',
        json_pointer='/url'
    )
).add(
    'foaf:isPrimaryTopicOf',
    DATASET_CATALOG_RECORD
).add(
    'dct:accrualPeriodicity',
    Enum(
        [
            ('unknown', "onbekend"),
            ('realtime', "continu"),
            ('day', "dagelijks"),
            ('2pweek', "twee keer per week"),
            ('week', "wekelijks"),
            ('2weeks', "tweewekelijks"),
            ('month', "maandelijks"),
            ('quarter', "eens per kwartaal"),
            ('2pyear', "halfjaarlijks"),
            ('year', "jaarlijks"),
            ('2years', "tweejaarlijks"),
            ('4years', "vierjaarlijks"),
            ('5years', "vijfjaarlijks"),
            ('10years', "tienjaarlijks"),
            ('reg', "regelmatig"),
            ('irreg', "onregelmatig"),
            ('req', "op afroep"),
            ('other', "anders")
        ],
        title="Wijzigingsfrequentie",
        default='unknown',
        json_pointer='/frequency',
        mapping=(
            lambda x: {
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
                'halfjaarlijks': '2pyear',
                'jaarlijks': 'year',
                'kleinschalige topografie: jaarlijks, grootschalige topografie: maandelijks': 'month',
                'maandelijks': 'month',
                'om de 10 jaar': '10years',
                'onregelmatig': 'irreg',
                'op afroep': 'req',
                'wekelijks': 'week',
                'dagen': '2pweek'
            }[(x or '').strip()]
        )
        # description="Frequentie waarmee de gegevens worden geactualiseerd"
    )
).add(
    'dct:temporal',
    Object(
        title="",
        json_pointer='/foobar'
        # description="De tijdsperiode die de gegevensset beslaat"
    ).add(
        'time:hasBeginning',
        dcat.Date(
            title="Tijdsperiode van",
            description="Geef de tijdsperiode aan (begindatum), die de gegevensset beslaat."
        )
    ).add(
        'time:hasEnd',
        dcat.Date(
            title="Tijdsperiode tot",
            description="Geef de tijdsperiode aan (einddatum), die de gegevensset beslaat."
        )
    )
).add(
    'ams:temporalUnit',
    Enum(
        [
            ('na', "Geen tijdseenheid"),
            ('realtime', "Realtime"),
            ('minutes', "Minuten"),
            ('hours', "Uren"),
            ('parttime', "Dagdelen"),
            ('days', "Dagen"),
            ('weeks', "Weken"),
            ('months', "Maanden"),
            ('quarters', "Kwartalen"),
            ('years', "Jaren"),
            ('other', "anders")
        ],
        title="Tijdseenheid",
        json_pointer='/tijdseenheid',
        default='na',
        required=True,
        mapping=(
            lambda x:
            {
                None: 'na',
                'Geen tijdseenheid': 'na',
                'Minuten': 'minutes',
                'Uren': 'hours',
                'Dagen': 'days',
                'Maanden': 'months',
                'Kwartalen': 'quarters',
                'Jaren': 'years'
            }[x]
        )
        # description="Geef de tijdseenheid aan waarin de gegevensset is uitgedrukt, indien van toepassing."
    )
).add(
    'ams:spatialDescription',
    PlainTextLine(
        title="Omschrijving gebied",
        json_pointer='/spatial'
    )
).add(
    'dct:spatial',
    PlainTextLine(
        title="Coördinaten gebiedskader",
        json_pointer='/foobar',
        description="Beschrijving of coördinaten van het gebied dat de gegevensset bestrijkt (boundingbox). Rijksdriehoeksstelsel (pseudo-RD)"
    )
).add(
    'ams:spatialUnit',
    Enum(
        [
            ('na', "Geen geografie"),
            ('specific', "Specifieke punten/vlakken/lijnen"),
            ('nation', "Land"),
            ('region', "Regio"),
            ('city', "Gemeente"),
            ('district', "Stadsdeel"),
            ('area', "Gebied"),
            ('borrow', "Wijk"),
            ('neighborhood', "Buurt"),
            ('block', "Bouwblok"),
            ('zip4', "Postcode (4 cijfers)"),
            ('zip5', "Postcode (4 cijfers, 1 letter)"),
            ('zip6', "Postcode (4 cijfers, 2 letters)"),
            ('other', "anders")
        ],
        default='na',
        title="Gebiedseenheid",
        json_pointer='/gebiedseenheid',
        mapping=(
            lambda x:
            {
                None: None,
                'Geen geografie': None,
                'Buurt': 'neighborhood',
                'Gemeente': 'city',
                'Land': 'nation',
                'Regio': 'region',
                'Specifieke punten/vlakken/lijnen': 'specific',
                'Stadsdeel': 'district'
            }[x]
        )
        # description="Geef een eenheid van het gebied waarin de gegevensset is uitgedrukt."
    )
).add(
    'overheid:grondslag',
    Markdown(
        title="Juridische grondslag",
        description="Geef indien van toepassing aan wat is de oorspronkelijke juridische basis is van de gegevensset.",
        json_pointer='/foobar'
    )
).add(
    'dct:language',
    Enum(
        [
            ('lang1:nl', "Nederlands"),
            ('lang1:en', "Engels")
        ],
        mapping=(lambda x: 'lang1:nl'),
        json_pointer='',
        title="Taal",
        # description="De taal van de gegevensset",
        default='lang1:nl',
        required=True
    )
).add(
    'ams:owner',
    PlainTextLine(
        title="Eigenaar",
        description="Eigenaar en verantwoordelijke voor de betreffende registratie, ook wel bronhouder genoemd. Bij de overheid is dit het bestuursorgaan of rechtspersoon aan wie bij wettelijk voorschrift de verantwoordelijkheid voor het bijhouden van gegevens in een registratie is opgedragen.",
        examples=constants.OWNERS,
        json_pointer='/organization/title'
    )
).add(
    'dcat:contactPoint',
    CONTACT_POINT
).add(
    'dct:publisher',
    DCT_PUBLISHER
).add(
    'dcat:theme',
    List(
        Enum(
            constants.THEMES,
            mapping=_ckan_2_dcat_theme_mapper,
            json_pointer=''
        ),
        title="Thema",
        required=True,
        unique_items=True,
        json_pointer='/groups'
        # description="Geef aan onder welke hoofdthema’s de gegevensset valt."
    ),
).add(
    'dcat:keyword',
    List(
        PlainTextLine(
            examples=constants.KEYWORD_EXAMPLES,
            json_pointer='/name'
        ),
        title="Tags",
        unique_items=True,
        json_pointer='/tags'
        # description="Geef een aantal trefwoorden, die van toepassing zijn op de gegevensset, zodat de gegevensset gevonden kan worden."
    )
).add(
    'ams:license',
    Enum(
        constants.LICENSES,
        title="Licentie",
        description="Geef aan onder welke open data licentie de gegevensset gepubliceerd is, indien van toepassing. Gebruik invulhulp om licentie te bepalen. Indien er sprake is van een gedeeltelijk publieke dataset, dan geldt de licentie voor het publieke deel.",
        required=True,
        default='unspec',
        json_pointer='/license_id',
        mapping=(
            lambda x:
            x if x in {'cc-by', 'cc-nc', 'cc-zero', 'other-open'}
            else 'cc-by-nc-nd' if x in {'cc_by-nc-nd'}
            else 'cc-by' if x in {'cc_by'}
            else 'unspec' if x in {'niet-gespecificeerd', 'notspecified'}
            else 'cc-zero' if x in {'publiek'}
            else None
        )
    )
).add(
    'dct:identifier',
    PlainTextLine(
        title="UID",
        description="Unieke identifier",
        json_pointer='/id'
    )
)


# def _from_ckan(data: dict):
#     original = resolve_pointer(data, DATASET.json_pointer, None)
#     if original is None:
#         return None
#     assert isinstance(original, dict)
#     retval = {}
#     for (name, value) in DATASET.properties:
#         v = value.from_ckan(original)
#         if v is not None:
#             retval[name] = v
#     def distribution_filter(distribution):
#         if 'dcat:accessURL' not in distribution:
#             logger.error(
#                 "No dcat:accessURL is distribution %s of dataset %s",
#                 distribution['title']
#             )
#             return None
#     return retval if len(retval) else None
