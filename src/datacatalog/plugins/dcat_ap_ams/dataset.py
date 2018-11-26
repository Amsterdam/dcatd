from . import constants
from .fieldtypes import *
from .distribution import DISTRIBUTION
from .logger import logger


DATASET = dcat.Object().add(
    'dct:title',
    dcat.PlainTextLine(
        title="Titel",
        # description="Geef een titel van de gegevensset.",
        required='Geen titel opgegeven'
    )
).add(
    'dct:description',
    Markdown(
        title="Beschrijving",
        description="Geef een samenvatting van de inhoud van de gegevensset, welke gegevens zitten erin en wat is expliciet eruit gelaten",
        required='Geen beschrijving opgegeven'
    )
).add(
    'dcat:distribution',
    dcat.List(
        DISTRIBUTION,
        title="Resources",
        required=[]
    )
).add(
    'overheidds:doel',
    Markdown(
        title="Doel",
        required="Geen doel gedefiniëerd",
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
    dcat.Object(
        required=dict(),
        title="",  # TODO: This was probably a front-end requirement, but it's ugly.
        read_only=True
    ).add(
        'dct:issued',
        dcat.Date(
            title="Publicatiedatum",
            description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld",
            required='1970-01-01'  # datetime.date.today().isoformat()
        )
    ).add(
        'dct:modified',
        dcat.Date(
            title="Wijzigingsdatum",
            description="De datum waarop deze beschrijving van de gegevensset voor het laatst is gewijzigd",
            required='1970-01-01'  # datetime.date.today().isoformat()
        )
    )
).add(
    'dct:accrualPeriodicity',
    dcat.Enum(
        constants.ACCRUAL_PERIODICITY,
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
        constants.TEMPORAL_UNIT,
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
        constants.SPACIAL_UNITS,
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
        required='lang1:nl'
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
        required=[],
        # TODO: allow_empty=False (afstemmen met Front-end)
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
        required=[]
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
        description="Unieke identifier",
        read_only=True
    )
).add(
    'ams:sort_modified',
    dcat.Date(
        title="Sorteerdatum",
        read_only=True
    )
).add(
    'ams:status',
    dcat.Enum(
        constants.STATUSES,
        title="Status",
        description="Beschikbaar of anders",
        required='beschikbaar',
        default='gepland'
    )
)
