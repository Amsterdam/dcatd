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
        required='Titel onbekend'
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
        required=''
    )
).add(
    'ams:purl',
    dcat.String(
        format='uri',
        title="Persistente URL",
        description="Persistente URL voor deze resource.",
        read_only=True,
        required=''
    )
).add(
    'ams:resourceType',
    dcat.Enum(
        constants.RESOURCE_TYPES,
        title="Type resource",
        required='data'
    )
).add(
    'ams:distributionType',
    dcat.Enum(
        constants.DISTRIBUTION_TYPES,
        title="Verschijningsvorm",
        required='file'
    )
).add(
    'ams:serviceType',
    dcat.Enum(
        constants.SERVICE_TYPES,
        title="Type API/Service",
        description="Geef het type API of webservice"
    )
).add(
    'dct:format',
    # TODO: Vervangen door dcat:mediaType, en evt. inzetten in plaats van ams:serviceType
    dcat.Enum(
        constants.DCT_FORMATS,
        title="Type bestand"
    )
).add(
    'dcat:mediaType',
    dcat.Enum(
        constants.DCT_FORMATS,
        title="Type bestand",
        description="Dit is het juiste veld, volgens de DCAT standaard. Wij gebruiken dct:format, maar dat moet anders.",
        read_only=True
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
    )
).add(
    'dc:identifier',
    dcat.PlainTextLine(
        title="UID",
        description="Unieke identifier",
        required=''
    )
).add(
    'ams:classification',
    dcat.Enum(
        constants.CLASSIFICATIONS,
        title="Classification"
    )
).add(
    'dcat:byteSize',
    dcat.Integer(
        minimum=1,
        title="Bestandsgrootte",
        description="Bestandsgrootte in bytes"
    )
).add(
    'foaf:isPrimaryTopicOf',
    dcat.Object(
        required=dict(),
        read_only=True,
        # TODO: Probably a front-end requirement, but really ugly:
        title=""
    ).add(
        'dct:issued',
        dcat.Date(
            title="Publicatiedatum",
            description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld",
            required='1970-01-01'
        )
    ).add(
        'dct:modified',
        dcat.Date(
            title="Wijzigingsdatum",
            description="De datum waarop deze beschrijving van de gegevensset voor het laatst is gewijzigd",
            required='1970-01-01'
        )
    )
)
