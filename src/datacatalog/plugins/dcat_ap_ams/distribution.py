from . import constants
from .fieldtypes import *
# from .logger import logger


def _serviceType_mapping(data: dict) -> T.Optional[str]:
    if data['resource_type'] != 'api':
        return None
    ckan_format = data.get('format', '').lower()
    return ckan_format if ckan_format in ('wms', 'wfs') else 'other'


DISTRIBUTION = Object(json_pointer='').add(
    'dct:title',
    PlainTextLine(
        title="Titel",
        required=True,
        json_pointer='/name'
    )
).add(
    'dct:description',
    Markdown(
        from_='html',
        title="Beschrijving",
        json_pointer='/description'
    )
).add(
    'dcat:accessURL',
    String(
        format='uri',
        title="URL",
        description="Link naar de daadwerkelijke gegevensset",
        required=True,
        json_pointer='/url'
    )
).add(
    'ams:resourceType',
    Enum(
        [
            ('data', "Data"),
            ('doc', "Documentatie"),
            ('vis', "Visualisatie"),
            ('app', "Voorbeeldtoepassing")
        ],
        title="Type resource",
        required=True,
        json_pointer='/type',
        mapping=(
            lambda x: {
                'Data': 'data',
                'Documentatie': 'doc',
                'Weergave': 'vis',
                'Toepassingen': 'app'
            }.get(x, 'data')
        )
    )
).add(
    'ams:distributionType',
    Enum(
        [
            ('api', "API/Service"),
            ('file', "Bestand"),
            ('web', "Website")
        ],
        title="Verschijningsvorm",
        required=True,
        json_pointer='/resource_type',
        mapping=(
            lambda x: {
                'api': 'api',
                'file': 'file',
                'file.upload': 'file'
            }.get(x, 'file')
        )
    )
).add(
    'ams:serviceType',
    Enum(
        [
            ('atom', "REST: Atom feed"),
            ('rest', "REST: overig"),
            ('csw', "CSW"),
            ('wcs', "WCS"),
            ('wfs', "WFS"),
            ('wms', "WMS"),
            ('wmts', "WMTS"),
            ('soap', "SOAP"),
            ('other', "Anders")
        ],
        title="Type API/Service",
        description="Geef het type API of webservice",
        json_pointer='',
        mapping=_serviceType_mapping
    )
).add(
    'dct:format',
    Enum(
        [
            ('n/a', ""),
            ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', "xlsx"),
            ('application/pdf', "pdf"),
            ('text/csv', "csv"),
            ('application/json', "json"),
            ('application/vnd.geo+json', "geojson"),
            ('application/zip; format="shp"', "shp"),
            ('application/xml', "xml"),
            ('application/octet-stream', "anders"),
        ],
        title="Type bestand",
        json_pointer='/format',
        mapping=(
            lambda x: constants.DCT_FORMATS.get(x.lower(), 'application/octet-stream')
        )
    )
).add(
    'ams:layerIdentifier',
    PlainTextLine(
        title="Interne Kaartlaag ID",
        description="De Citydata kaartlaag waarmee deze dataset op de kaart getoond kan worden",
        json_pointer='/foobar'
    )
).add(
    'dct:modified',
    Date(
        title="Verversingsdatum",
        description="De datum waarop de inhoud van deze link voor het laatst is geactualiseerd.",
        default=datetime.date.today().isoformat(),
        json_pointer='/last_modified'
    )
).add(
    'ams:classification',
    Enum(
        [
            ('public', "Publiek toegankelijk"),
        ],
        title="Classification",
        json_pointer='',
        mapping=(lambda x: 'public')
    )
).add(
    'dcat:byteSize',
    Integer(
        minimum=0,
        title="Bestandsgrootte",
        description="Bestandsgrootte in bytes",
        json_pointer='/size'
    )
).add(
    'foaf:isPrimaryTopicOf',
    Object(
        required=True,
        title="",
        json_pointer=''
    ).add(
        'dct:issued',
        Date(
            title="Publicatiedatum",
            description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld",
            default=datetime.date.today().isoformat(),
            json_pointer='/created'
        )
    ).add(
        'dct:modified',
        Date(
            title="Wijzigingsdatum",
            description="De datum waarop deze beschrijving van de gegevensset voor het laatst is gewijzigd",
            default=datetime.date.today().isoformat(),
            required=True,
            json_pointer='/last_modified'
        )
    )
)
