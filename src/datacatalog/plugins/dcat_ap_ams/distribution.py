import typing as T

from . import constants
from .fieldtypes import *
# from .logger import logger


def _serviceType_mapping(data: dict) -> T.Optional[str]:
    if data['resource_type'] != 'api':
        return None
    ckan_format = data.get('format', '').lower()
    return ckan_format if ckan_format in ('wms', 'wfs') else 'other'


DISTRIBUTION = dcat.Object().add(
    'dct:title',
    dcat.PlainTextLine(
        title="Titel",
        required=True
    )
).add(
    'dct:description',
    Markdown(
        title="Beschrijving"
    )
).add(
    'dcat:accessURL',
    dcat.String(
        format='uri',
        title="URL of upload",
        description="Toegangslink naar de daadwerkelijke gegevensset óf downloadlink om gegevensset te downloaden",
        required=True
    )
).add(
    'ams:resourceType',
    dcat.Enum(
        [
            ('data', "Data"),
            ('doc', "Documentatie"),
            ('vis', "Visualisatie"),
            ('app', "Voorbeeldtoepassing")
        ],
        title="Type resource",
        required=True
    )
).add(
    'ams:distributionType',
    dcat.Enum(
        [
            ('api', "API/Service"),
            ('file', "Bestand"),
            ('web', "Website")
        ],
        title="Verschijningsvorm",
        required=True
    )
).add(
    'ams:serviceType',
    dcat.Enum(
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
        description="Geef het type API of webservice"
    )
).add(
    'dct:format',
    dcat.Enum(
        constants.DCT_FORMATS,
        title="Type bestand"
    )
).add(
    'ams:layerIdentifier',
    dcat.PlainTextLine(
        title="Interne Kaartlaag ID",
        description="De Citydata kaartlaag waarmee deze dataset op de kaart getoond kan worden"
    )
).add(
    'dct:modified',
    dcat.Date(
        title="Verversingsdatum",
        description="De datum waarop de inhoud van deze link voor het laatst is geactualiseerd.",
        default=(lambda: datetime.date.today().isoformat())
    )
).add(
    'dc:identifier',
    dcat.PlainTextLine(
        title="UID",
        description="Unieke identifier"
    )
).add(
    'ams:classification',
    dcat.Enum(
        [
            ('public', "Publiek toegankelijk"),
        ],
        title="Classification"
    )
).add(
    'dcat:byteSize',
    dcat.Integer(
        minimum=0,
        title="Bestandsgrootte",
        description="Bestandsgrootte in bytes"
    )
).add(
    'foaf:isPrimaryTopicOf',
    dcat.Object(
        required=True,
        title=""
    ).add(
        'dct:issued',
        dcat.Date(
            title="Publicatiedatum",
            description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld",
            default=(lambda: datetime.date.today().isoformat())
        )
    ).add(
        'dct:modified',
        dcat.Date(
            title="Wijzigingsdatum",
            description="De datum waarop deze beschrijving van de gegevensset voor het laatst is gewijzigd",
            default=(lambda: datetime.date.today().isoformat()),
            sys_defined=True,
            required=True
        )
    )
)
