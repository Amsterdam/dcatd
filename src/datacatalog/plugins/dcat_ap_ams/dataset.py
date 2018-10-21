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


DATASET = dcat.Object().add(
    'dct:title',
    dcat.PlainTextLine(
        title="Titel",
        # description="Geef een titel van de gegevensset.",
        required=True
    )
).add(
    'dct:description',
    Markdown(
        title="Beschrijving",
        description="Geef een samenvatting van de inhoud van de gegevensset, welke gegevens zitten erin en wat is expliciet eruit gelaten",
        required=True
    )
).add(
    'dcat:distribution',
    dcat.List(
        DISTRIBUTION,
        title="Resources",
        default=[]
    )
).add(
    'overheidds:doel',
    Markdown(
        title="Doel",
        required=True,
        description="Geef aan met welk doel deze gegevensset is aangelegd. Waarom bestaat deze gegevensset?"
    )
).add(
    'dcat:landingPage',
    dcat.String(
        title="URL voor meer informatie",
        format='uri'
    )
).add(
    'foaf:isPrimaryTopicOf',
    DATASET_CATALOG_RECORD
).add(
    'dct:accrualPeriodicity',
    dcat.Enum(
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
        default='unknown'
        # description="Frequentie waarmee de gegevens worden geactualiseerd"
    )
).add(
    'dct:temporal',
    dcat.Object(
        title=""
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
    dcat.Enum(
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
        default='na',
        required=True
        # description="Geef de tijdseenheid aan waarin de gegevensset is uitgedrukt, indien van toepassing."
    )
).add(
    'ams:spatialDescription',
    dcat.PlainTextLine(
        title="Omschrijving gebied"
    )
).add(
    'dct:spatial',
    dcat.PlainTextLine(
        title="Coördinaten gebiedskader",
        description="Beschrijving of coördinaten van het gebied dat de gegevensset bestrijkt (boundingbox). Rijksdriehoeksstelsel (pseudo-RD)"
    )
).add(
    'ams:spatialUnit',
    dcat.Enum(
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
        title="Gebiedseenheid"
        # description="Geef een eenheid van het gebied waarin de gegevensset is uitgedrukt."
    )
).add(
    'overheid:grondslag',
    Markdown(
        title="Juridische grondslag",
        description="Geef indien van toepassing aan wat is de oorspronkelijke juridische basis is van de gegevensset."
    )
).add(
    'dct:language',
    dcat.Enum(
        [
            ('lang1:nl', "Nederlands"),
            ('lang1:en', "Engels")
        ],
        title="Taal",
        # description="De taal van de gegevensset",
        default='lang1:nl',
        required=True
    )
).add(
    'ams:owner',
    dcat.PlainTextLine(
        title="Eigenaar",
        description="Eigenaar en verantwoordelijke voor de betreffende registratie, ook wel bronhouder genoemd. Bij de overheid is dit het bestuursorgaan of rechtspersoon aan wie bij wettelijk voorschrift de verantwoordelijkheid voor het bijhouden van gegevens in een registratie is opgedragen."
        # examples=constants.OWNERS
    )
).add(
    'dcat:contactPoint',
    CONTACT_POINT
).add(
    'dct:publisher',
    DCT_PUBLISHER
).add(
    'dcat:theme',
    dcat.List(
        dcat.Enum(
            constants.THEMES
        ),
        title="Thema",
        required=True,
        unique_items=True
        # description="Geef aan onder welke hoofdthema’s de gegevensset valt."
    ),
).add(
    'dcat:keyword',
    dcat.List(
        dcat.PlainTextLine(
            examples=constants.KEYWORD_EXAMPLES
        ),
        title="Tags",
        unique_items=True,
        default=[]
        # description="Geef een aantal trefwoorden, die van toepassing zijn op de gegevensset, zodat de gegevensset gevonden kan worden."
    )
).add(
    'ams:license',
    dcat.Enum(
        constants.LICENSES,
        title="Licentie",
        description="Geef aan onder welke open data licentie de gegevensset gepubliceerd is, indien van toepassing. Gebruik invulhulp om licentie te bepalen. Indien er sprake is van een gedeeltelijk publieke dataset, dan geldt de licentie voor het publieke deel.",
        required=True,
        default='unspec'
    )
).add(
    'dct:identifier',
    dcat.PlainTextLine(
        title="UID",
        description="Unieke identifier"
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
