import json

from datacatalog.plugins.dcat import types as dcat


class Markdown(dcat.String):
    def __init__(self, *args, format=None, **kwargs):
        assert format is None
        super().__init__(*args, format='markdown', **kwargs)


LANGUAGE = dcat.Enum(
    [
        ('lang:nl', "Nederlands"),
        ('lang:en', "Engels")
    ],
    title="Taal",
    description="De taal van de gegevensset",
    default='lang:nl',
    required=True
)


THEME = dcat.Enum(
    [
        ('theme:bestuur-en-organisatie', "Bestuur en organisatie"),
        ('theme:bevolking', "Bevolking"),
        ('theme:dienstverlening', "Dienstverlening"),
        ('theme:economie-haven', "Economie & Haven"),
        ('theme:educatie-jeugd-diversiteit', "Educatie, Jeugd & Diversiteit"),
        ('theme:energie', "Energie"),
        ('theme:geografie', "Geografie"),
        ('theme:milieu-water', "Milieu & Water"),
        ('theme:openbare-orde-veiligheid', "Openbare orde & veiligheid"),
        ('theme:openbare-ruimte-groen', "Openbare ruimte & groen"),
        ('theme:sport-recreatie', "Sport & recreatie"),
        ('theme:stedelijke-ontwikkeling', "Stedelijke ontwikkeling"),
        ('theme:toerisme-cultuur', "Toerisme & cultuur"),
        ('theme:verkeer-infrastructuur', "Verkeer & Infrastructuur"),
        ('theme:verkiezingen', "Verkiezingen"),
        ('theme:werk-inkomen', "Werk & Inkomen"),
        ('theme:wonen-leefomgeving', "Wonen & leefomgeving"),
        ('theme:zorg-welzijn', "Zorg & welzijn")
    ]
)


CONTACT_POINT = dcat.Object(
    title="Inhoudelijk contactpersoon",
    description="De contactpersoon voor eventuele vragen over de inhoud en kwaliteit van de gegevens",
    required=True
)
CONTACT_POINT.add(
    'vcard:fn',
    dcat.PlainTextLine(
        title="Naam",
        description="Naam inhoudelijk contactpersoon",
        required=True
    )
)
CONTACT_POINT.add(
    'vcard:hasEmail',
    dcat.String(
        format='email',
        title="Email",
        description="Email inhoudelijk contactpersoon"
    )
)
CONTACT_POINT.add(
    'vcard:hasURL',
    dcat.String(
        format='uri',
        title="Website",
        description="Website inhoudelijk contactpersoon"
    )
)


DCT_PUBLISHER = dcat.Object(
    title="Technisch contactpersoon",
    description="De contactpersoon voor technische vragen over de aanlevering. Dit kan dezelfde contactpersoon zijn als voor de inhoudelijke vragen.",
    required=True
)
DCT_PUBLISHER.add(
    'foaf:name',
    dcat.PlainTextLine(
        title="Naam",
        description="Naam technisch contactpersoon",
        required=True
    )
)
DCT_PUBLISHER.add(
    'foaf:mbox',
    dcat.String(
        format='email',
        title="Email",
        description="Email technisch contactpersoon"
    )
)
DCT_PUBLISHER.add(
    'foaf:homepage',
    dcat.String(
        format='uri',
        title="Website",
        description="Website technisch contactpersoon"
    )
)


DISTRIBUTION = dcat.Object()
DISTRIBUTION.add(
    'dct:title',
    dcat.PlainTextLine(
        title="Titel van de link naar de gegevensset",
        required=True
    )
)
DISTRIBUTION.add(
    'dct:description',
    Markdown(
        title="Omschrijving van de link",
        description="Geef een omschrijving van de link, kan specifieke aanvullende informatie geven",
        required=True
    )
)
# DISTRIBUTION.add(
#     'ams:serviceType',
#     dcat.Enum(
#         {
#             'Atom': "Atom feed",
#             'CSW': "CSW",
#             'WCS': "WCS",
#             'WFS': "WFS",
#             'WMS': "WMS",
#             'WMTS': "WMTS",
#             'REST': "REST",
#             'SOAP': "SOAP",
#             'other': "Anders"
#         },
#         title="Type API/Service",
#         description="Geef het type API of webservice"
#     )
# )
# DISTRIBUTION.add(
#     'ams:issued',
#     dcat.Date(
#         title="Publicatiedatum van de link naar de gegevensset",
#         required=True
#     )
# )
# DISTRIBUTION.add(
#     'ams:modified',
#     dcat.Date(
#         title="Wijzigingsdatum van de link naar de gegevensset",
#         required=True
#     )
# )
# DISTRIBUTION.add(
#     'dct:modified',
#     dcat.Date(
#         title="Verversingsdatum",
#         description="Geef de datum waarop de inhoud van deze link voor het laatst is geactualiseerd."
#     )
# )
DISTRIBUTION.add(
    'dct:license',
    dcat.Enum(
        [
            ('cc-by', "Creative Commons, Naamsvermelding"),
            ('cc-by-nc', "Creative Commons, Naamsvermelding, Niet-Commercieel"),
            ('cc-by-nc-nd', "Creative Commons, Naamsvermelding, Niet-Commercieel, Geen Afgeleide Werken"),
            ('cc-by-nc-sa', "Creative Commons, Naamsvermelding, Niet-Commercieel, Gelijk Delen"),
            ('cc-by-nd', "Creative Commons, Naamsvermelding, Geen Afgeleide Werken"),
            ('cc-by-sa', "Creative Commons, Naamsvermelding, Gelijk Delen"),
            ('cc-nc', "Creative Commons, Niet-Commercieel"),
            ('cc-zero', "Publiek Domein"),
            ('other-open', "Anders, Open"),
            ('other-by', "Anders, Naamsvermelding"),
            ('other-nc', "Anders, Niet Commercieel"),
            ('other-not-open', "Anders, Niet Open"),
            ('unspec', "Niet gespecificeerd")
        ],
        title="Licentie",
        description="Geef aan onder welke open data licentie de gegevensset gepubliceerd is, indien van toepassing. Gebruik invulhulp om licentie te bepalen.\\\nIndien er sprake is van een gedeeltelijk publieke dataset, dan geldt de licentie voor het publieke deel",
        required=True
    )
)
DISTRIBUTION.add(
    'dcat:accessURL',
    dcat.String(
        format='uri',
        title="Toegangs-URL",
        description="Toegangslink naar de daadwerkelijke gegevensset"
    )
)
DISTRIBUTION.add(
    'dcat:downloadURL',
    dcat.String(
        format='uri',
        title="Download URL",
        description="Downloadlink om gegevensset te downloaden"
    )
)
DISTRIBUTION.add(
    'dcat:mediaType',
    dcat.PlainTextLine(
        pattern=r'^[-\w.]+/[-\w.]+$',
        title="Bestandsformaat",
        description="Geef het formaat van de beschikbare leveringsvorm van de dataset"
    )
)
DISTRIBUTION.add(
    'dcat:byteSize',
    dcat.Integer(
        minimum=0,
        title="Bestandsgrootte",
        description="Bestandsgrootte in bytes"
    )
)


CATALOG_RECORD = dcat.Object(required=True)
CATALOG_RECORD.add(
    'dct:issued',
    dcat.Date(
        title="Publicatiedatum",
        description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld"
    )
)
CATALOG_RECORD.add(
    'dct:modified',
    dcat.Date(
        title="Wijzigingsdatum",
        description="De datum waarop deze beschrijving van de gegevensset voor het laatst is gewijzigd",
        required=True
    )
)


DATASET = dcat.Object()
DATASET.add(
    'dct:title',
    dcat.PlainTextLine(
        title="Titel",
        description="Geef een titel van de gegevensset.",
        required=True
    )
)
DATASET.add(
    'dct:description',
    Markdown(
        title="Beschrijving",
        description="Geef een samenvatting van de inhoud van de gegevensset, welke gegevens zitten erin en wat is expliciet eruit gelaten",
        required=True
    )
)
DATASET.add(
    'dct:identifier',
    dcat.PlainTextLine(
        title="ID",
        description="Unieke identifier"
    )
)
DATASET.add(
    'dcat:keyword',
    dcat.List(
        dcat.PlainTextLine(),
        title="Trefwoorden",
        description="Trefwoorden die van toepassing zijn op de gegevensset, zodat de gegevensset gevonden kan worden"
    )
)
DATASET.add(
    'dct:language',
    LANGUAGE
)
DATASET.add(
    'dcat:contactPoint',
    CONTACT_POINT
)
DATASET.add(
    'dct:Temporal',
    dcat.Object(
        title="Tijdsperiode",
        description="De tijdsperiode die de gegevensset beslaat"
    ).add(
        'time:hasBeginning',
        dcat.Date(
            title="Van",
            required=True
        )
    ).add(
        'time:hasEnd',
        dcat.Date(
            title="Tot",
            required=True
        )
    )
)
DATASET.add(
    'dct:Spatial',
    Markdown(
        title="Coördinaten gebiedskader",
        description="Beschrijving of coördinaten van het gebied dat de gegevensset bestrijkt (boundingbox). Rijksdriehoeksstelsel (pseudo-RD) (EPSG:28992)"
    )
)
DATASET.add(
    'dct:accrualPeriodicity',
    dcat.Enum(
        [
            # 0 continu
            # 1 dagelijks
            # 7 wekelijks
            # tweewekelijks
            # maandelijks
            # eens per kwartaal
            # halfjaarlijks
            # jaarlijks
            # tweejaarlijks
            # driejaarlijks
            # onregelmatig
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
            ('req', "op afroep")
        ],
        title="Wijzigingsfrequentie",
        description="Frequentie waarmee de gegevens worden geactualiseerd"
    )
)
DATASET.add(
    'dcat:theme',
    dcat.List(
        THEME,
        title="Thema’s",
        description="Geef aan onder welke hoofdthema’s de gegevensset valt."
    )
)
DATASET.add(
    'dct:publisher',
    DCT_PUBLISHER
)
DATASET.add(
    'overheidds:doel',
    Markdown(
        title="Doel",
        description="Geef aan met welk doel deze gegevensset is aangelegd. Waarom bestaat deze gegevensset?",
        required=True
    )
)
DATASET.add(
    'dcat:distribution',
    dcat.List(
        DISTRIBUTION,
        title="Resources",
        required=True
    )
)
DATASET.add(
    'foaf:isPrimaryTopicOf',
    CATALOG_RECORD
)


print(json.dumps(
    DATASET.schema,
    indent='  ', sort_keys=True
))
