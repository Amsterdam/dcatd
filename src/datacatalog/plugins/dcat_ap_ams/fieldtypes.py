import datetime
import re
# import subprocess
import typing as T

import bleach
from jsonpointer import resolve_pointer

from datacatalog import dcat


class Date(dcat.Date):
    def __init__(self, *args, json_pointer: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_pointer = json_pointer

    def from_ckan(self, data: dict) -> T.Optional[str]:
        original = resolve_pointer(data, self.json_pointer, None)
        if original is None:
            return None
        assert re.fullmatch(r'\d\d\d\d-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?', original)
        return original[:10]


class Enum(dcat.Enum):
    def __init__(self, *args, mapping: T.Callable, json_pointer: str, **kwargs):
        # language=rst
        """

        Parameter ``mapping`` must be a callable with signature ``foo(key)``,
        e.g. :meth:`dict.get`.

        """
        super().__init__(*args, **kwargs)
        self.mapping = mapping
        self.json_pointer = json_pointer

    def from_ckan(self, data: dict) -> T.Optional[str]:
        original = resolve_pointer(data, self.json_pointer, None)
        return self.mapping(original)


class Integer(dcat.Integer):
    def __init__(self, *args, json_pointer: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_pointer = json_pointer

    def from_ckan(self, data: dict) -> T.Optional[int]:
        retval = resolve_pointer(data, self.json_pointer, None)
        if retval is not None:
            retval = int(retval)
        return retval


class List(dcat.List):
    def __init__(self, *args, json_pointer: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_pointer = json_pointer

    def from_ckan(self, data: T.Iterable):
        original = resolve_pointer(data, self.json_pointer, None)
        if original is None:
            return None
        assert isinstance(original, list)
        retval = []
        for item in original:
            v = self.item_type.from_ckan(item)
            if v is not None:
                retval.append(v)
        return retval


class Object(dcat.Object):
    def __init__(self, *args, json_pointer: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_pointer = json_pointer

    def from_ckan(self, data: dict) -> T.Optional[dict]:
        original = resolve_pointer(data, self.json_pointer, None)
        if original is None:
            return None
        assert isinstance(original, dict)
        retval = {}
        for (name, value) in self.properties:
            v = value.from_ckan(original)
            if v is not None:
                retval[name] = v
        return retval if len(retval) else None


class PlainTextLine(dcat.PlainTextLine):
    def __init__(self, *args, json_pointer: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_pointer = json_pointer

    def from_ckan(self, data: dict) -> T.Optional[str]:
        return resolve_pointer(data, self.json_pointer, None)


class String(dcat.String):
    def __init__(self, *args, json_pointer: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_pointer = json_pointer

    def from_ckan(self, data: dict) -> T.Optional[str]:
        original = resolve_pointer(data, self.json_pointer, None)
        return original or None


class Markdown(String):
    def __init__(self, *args, format=None, from_=None, **kwargs):
        assert format is None
        super().__init__(*args, **kwargs)
        self.from_ = from_

    def from_ckan(self, data: dict) -> T.Optional[str]:
        original = super().from_ckan(data)
        if original is None or self.from_ is None:
            return original
        # TODO replace this line...
        return original
        # TODO with these lines:
        # return subprocess.run(
        #     ['pandoc', '-f', self.from_, '-t', 'markdown'],
        #     input=original.encode(), stdout=subprocess.PIPE, check=True
        # ).stdout.decode()

    def full_text_search_representation(self, data: str):
        return bleach.clean(data, tags=[], strip=True)


CONTACT_POINT = Object(
    required=True,
    title="",
    json_pointer=''
).add(
    'vcard:fn',
    PlainTextLine(
        description="Geef de naam van de contactpersoon voor eventuele vragen over de inhoud en kwaliteit van de gegevens.",
        title="Inhoudelijke contactpersoon",
        required=True,
        json_pointer='/contact_name'
    )
).add(
    'vcard:hasEmail',
    String(
        format='email',
        title="E-mail inhoudelijke contactpersoon",
        json_pointer='/contact_email'
    )
).add(
    'vcard:hasURL',
    String(
        format='uri',
        title="Website inhoudelijke contactpersoon",
        # description="Website inhoudelijk contactpersoon"
        json_pointer='/contact_uri'
    )
)


DCT_PUBLISHER = Object(
    required=True,
    title="",
    json_pointer=''
).add(
    'foaf:name',
    PlainTextLine(
        title="Technische contactpersoon",
        description="Geef de naam van de contactpersoon voor technische vragen over de aanlevering. Dit kan dezelfde contactpersoon zijn als voor de inhoudelijke vragen.",
        required=True,
        json_pointer='/publisher'
    )
).add(
    'foaf:mbox',
    String(
        format='email',
        title="E-mail technische contactpersoon",
        # description="Email technisch contactpersoon"
        json_pointer='/publisher_email'
    )
).add(
    'foaf:homepage',
    String(
        format='uri',
        title="Website technische contactpersoon",
        # description="Website technisch contactpersoon"
        json_pointer='/publisher_uri'
    )
)


DATASET_CATALOG_RECORD = Object(
    required=True,
    title="",
    json_pointer=''
).add(
    'dct:issued',
    Date(
        title="Publicatiedatum",
        description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld",
        default=datetime.date.today().isoformat(),
        json_pointer='/metadata_created'
    )
).add(
    'dct:modified',
    Date(
        title="Wijzigingsdatum",
        description="De datum waarop deze beschrijving van de gegevensset voor het laatst is gewijzigd",
        default=datetime.date.today().isoformat(),
        required=True,
        json_pointer='/metadata_modified'
    )
)
