import datetime

import bleach

from datacatalog import dcat


class Markdown(dcat.String):
    def __init__(self, *args, format=None, **kwargs):
        assert format is None
        super().__init__(*args, **kwargs)

    def full_text_search_representation(self, data: str):
        return bleach.clean(data, tags=[], strip=True)


CONTACT_POINT = dcat.Object(
    required=True,
    title=""
).add(
    'vcard:fn',
    dcat.PlainTextLine(
        description="Geef de naam van de contactpersoon voor eventuele vragen over de inhoud en kwaliteit van de gegevens.",
        title="Inhoudelijk contactpersoon",
        required=True
    )
).add(
    'vcard:hasEmail',
    dcat.String(
        format='email',
        title="E-mail inhoudelijk contactpersoon"
    )
).add(
    'vcard:hasURL',
    dcat.String(
        format='uri',
        title="Website inhoudelijk contactpersoon"
        # description="Website inhoudelijk contactpersoon"
    )
)


DCT_PUBLISHER = dcat.Object(
    required=True,
    title=""
).add(
    'foaf:name',
    dcat.PlainTextLine(
        title="Technisch contactpersoon",
        description="Geef de naam van de contactpersoon voor technische vragen over de aanlevering. Dit kan dezelfde contactpersoon zijn als voor de inhoudelijke vragen.",
        required=True
    )
).add(
    'foaf:mbox',
    dcat.String(
        format='email',
        title="E-mail technisch contactpersoon"
        # description="Email technisch contactpersoon"
    )
).add(
    'foaf:homepage',
    dcat.String(
        format='uri',
        title="Website technisch contactpersoon"
        # description="Website technisch contactpersoon"
    )
)


DATASET_CATALOG_RECORD = dcat.Object(
    required=True,
    title=""
).add(
    'dct:issued',
    dcat.Date(
        title="Publicatiedatum",
        description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld",
        default=datetime.date.today().isoformat()
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
