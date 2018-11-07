import typing as T
import logging

# import jsonpointer
import jsonschema


logger = logging.getLogger(__name__)


class Type(object):
    def __init__(self, *args,
                 title: T.Optional[str]=None,
                 description: T.Optional[str]=None,
                 required: T.Optional[T.Any]=None,
                 default: T.Optional[T.Any]=None,
                 examples: T.Optional[T.List[str]]=None,
                 format: T.Optional[str]=None,
                 read_only: bool=False):
        # language=rst
        """
        If either ``read_only_get`` or ``read_only_put`` is provided, the type is automatically marked as ``readOnly`` in the JSON Schema.

        :param args: Unused. It’s only part of the signature so that the
            implementation can force callers to use named arguments only.
        :param title: Copied verbatim into JSON Schema
        :param description: Copied verbatim into JSON Schema
        :param required: Some default value, for GET requests where this value
            is still empty.
        :param default: Copied verbatim into JSON Schema. For documentation only.
        :param examples: Copied verbatim into JSON Schema
        :param format: Copied verbatim into JSON Schema
        :param read_only: For documentation only. Fields marked as read_only
            will only be in the openapi schema for ``GET`` methods, and marked
            as ``readOnly``.
        """
        if len(args) > 0:
            raise ValueError()
        self.title = title
        self.description = description
        self.required = required
        self.default = default
        self.examples = examples
        self.format = format
        assert isinstance(read_only, bool)
        self.read_only = read_only

    def schema(self, method: str) -> dict:
        retval = {}
        if self.title is not None:
            retval['title'] = self.title
        if self.description is not None:
            retval['description'] = self.description
        if self.default is not None:
            retval['default'] = self.default
        if self.examples is not None:
            retval['examples'] = self.examples
        if self.format is not None:
            retval['format'] = self.format
        if self.read_only is not None:
            retval['readOnly'] = self.read_only
        return retval

    def full_text_search_representation(self, data) -> T.Optional[str]:
        return None

    def validate(self, data: dict, method: str):
        # language=rst
        """Validate the data.

        :returns: the Type for which validation succeeded. See also
            :meth:`OneOf.validate`
        :rtype: Type

        """
        jsonschema.validate(data, self.schema(method))
        return self

    def canonicalize(self, value: T.Any):
        return value


class List(Type):
    def __init__(self,
                 item_type: Type,
                 *args,
                 required=None,
                 default=None,
                 format=None,
                 allow_empty=True,
                 unique_items: T.Optional[bool]=None,
                 **kwargs):
        assert format is None
        # Not sure if the next statement is useful, but it probably won't do any
        # harm:
        if default is None and required is not None and allow_empty:
            default = required
        super().__init__(*args, required=required, default=default, **kwargs)
        self.item_type = item_type
        self.allow_empty = allow_empty
        self.unique_items = unique_items

    def schema(self, method: str) -> dict:
        retval = dict(super().schema(method))  # Important: makes a shallow copy.
        retval.update({
            'type': 'array',
            'items': self.item_type.schema(method)
        })
        if self.unique_items is not None:
            retval['uniqueItems'] = bool(self.unique_items)
        if not self.allow_empty:
            retval['minItems'] = 1
        return retval

    def canonicalize(self, value: T.Optional[list]):
        value = super().canonicalize(value)
        if value is None:
            return None
        if not isinstance(value, list):
            raise TypeError("{}: not a list".format(value))
        retval = []
        for index, datum in enumerate(value):
            v = self.item_type.canonicalize(datum)
            if v is not None:
                retval.append(v)
        return retval

    def full_text_search_representation(self, data: T.Iterable):
        """We must check whether the given data is really a list, jsonld may
        flatten lists."""
        if type(data) is list:
            retval = '\n\n'.join([
                self.item_type.full_text_search_representation(v)
                for v in data if v is not None
            ])
            return retval if len(retval) > 0 else None
        return self.item_type.full_text_search_representation(data)


# class OneOf(Type):
#     def __init__(self, *types, **kwargs):
#         super().__init__(**kwargs)
#         self.types = list(types)
#
#     def schema(self, method: str) -> dict:
#         retval = dict(super().schema(method))  # Important: makes a shallow copy
#         retval['oneOf'] = [v.schema(method) for v in self.types]
#         return retval
#
#     def validate(self, data, method) -> Type:
#         for type in self.types:
#             try:
#                 jsonschema.validate(data, self.schema(method))
#                 return type
#             except jsonschema.ValidationError:
#                 pass
#         raise jsonschema.ValidationError("Not valid for any type")
#
#     def full_text_search_representation(self, data: T.Any):
#         raise NotImplementedError()
#
#     def canonicalize(self, data: T.Any, **kwargs):
#         return self.validate(data).canonicalize(data, **kwargs)


class Object(Type):
    def __init__(self, *args, format=None, **kwargs):
        assert format is None
        super().__init__(*args, **kwargs)
        self.properties: T.List[T.Tuple[str, Type]] = []

    @property
    def property_names(self):
        return [x[0] for x in self.properties]

    def __getitem__(self, item):
        for name, value in self.properties:
            if name == item:
                return value
        raise KeyError()

    def add(self, name, value, before=None):
        if name in self.property_names:
            raise ValueError()
        property = (name, value)
        if before is None:
            self.properties.append(property)
        else:
            insert_position = self.property_names.index(before)
            self.properties.insert(insert_position, property)
        return self

    def schema(self, method: str) -> dict:
        retval = dict(super().schema(method))  # Important: makes a shallow copy
        # Also show read_only properties in the frontend because they ned to be shown
        # TODO : In frontend use read_only flag in schema to make properties readonly
        properties = self.properties

        retval.update({
            'type': 'object',
            'properties': {
                name: value.schema(method)
                for name, value in properties
            },
            'x-order': [name for name, value in properties]
        })
        required = list(
            name
            for name, type_ in properties
            if type_.required is not None
        )
        if len(required) > 0:
            retval['required'] = required
        return retval

    def full_text_search_representation(self, data: dict):
        ftsr = (
            value.full_text_search_representation(data[key])
            for key, value in self.properties
            if key in data
        )
        retval = '\n\n'.join(v for v in ftsr if v is not None)
        return retval if len(retval) > 0 else None

    def canonicalize(self, value: T.Optional[dict]):
        value = super().canonicalize(value)
        if value is None:
            return None
        if not isinstance(value, dict):
            raise TypeError("{}: not a dict".format(value))
        retval = {}
        for key, type_ in self.properties:
            if key not in value:
                continue
            v = type_.canonicalize(value[key])
            if v is not None:
                retval[key] = v
        return retval

    def set_required_values(self, object_: dict) -> dict:
        # language=rst
        """
        This method is called only during GET requests, just before the body is
        returned to the user.

        :param object_: The object about to be returned to the user.
        :return: ``object_`` with required values added.
        """
        retval = dict(object_)  # Important. Makes a shallow copy.
        for key, type_ in self.properties:
            if type_.required is not None and key not in retval:
                retval[key] = type_.required
            if isinstance(type_, Object) and key in retval:
                retval[key] = type_.set_required_values(retval[key])
        return retval


class String(Type):
    def __init__(self, *args, pattern=None, max_length=None, allow_empty=False,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern = pattern
        self.max_length = max_length
        self.allow_empty = allow_empty

    def schema(self, method: str) -> dict:
        retval = dict(super().schema(method))  # Important: makes a shallow copy
        retval['type'] = 'string'
        if self.pattern is not None:
            retval['pattern'] = self.pattern
        if self.max_length is not None:
            retval['maxLength'] = self.max_length
        if not self.allow_empty:
            retval['minLength'] = 1
        return retval

    def full_text_search_representation(self, data: str):
        return data

    def canonicalize(self, value: T.Optional[str]):
        value = super().canonicalize(value)
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("{}: not a string".format(repr(value)))
        value = value.strip().replace('\r\n', '\n')
        if len(value) == 0 and not self.allow_empty:
            value = None
        return value


class PlainTextLine(String):
    def __init__(self, *args, pattern=None, **kwargs):
        assert pattern is None
        super().__init__(*args, pattern=r'^[^\n\r]*?\S[^\n\r]*$', **kwargs)


class Date(String):
    def __init__(self, *args, format=None, pattern=None, **kwargs):
        assert format is None and pattern is None
        super().__init__(*args,
                         format='date',
                         pattern=r'^\d\d\d\d-[01]\d-[0-3]\d(?:T[012]\d:[0-5]\d:[0-5]\d(?:\.\d+)?)?(?:Z|[01]\d(?::[0-5]\d)?)?$',
                         **kwargs)

    def canonicalize(self, value: T.Optional[str]) -> T.Optional[str]:
        value = super().canonicalize(value)
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("{}: not a string".format(repr(value)))
        return value[:10]


class Language(String):
    def __init__(self, *args, format=None, pattern=None, **kwargs):
        assert format is None and pattern is None
        super().__init__(*args,
                         format='lang',
                         pattern=r'^(?:lang1:\w\w|lang2:\w\w\w)$',
                         **kwargs)


class Enum(String):
    def __init__(self, values, *args, allow_empty=None, **kwargs):
        assert allow_empty is None
        super().__init__(*args, **kwargs)
        self.values = values
        self.dict = {key: value for key, value in values}

    def schema(self, method: str) -> dict:
        retval = dict(super().schema(method))  # Important: makes a shallow copy
        retval['enum'] = [v[0] for v in self.values]
        retval['enumNames'] = [v[1] for v in self.values]
        return retval

    def full_text_search_representation(self, data: str):
        return self.dict[data]


class Integer(Type):
    def __init__(self, *args, multipleOf=None,
                 maximum=None, exclusiveMaximum=None,
                 minimum=None, exclusiveMinimum=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.multipleOf = multipleOf
        self.maximum = maximum
        self.exclusiveMaximum = exclusiveMaximum
        self.minimum = minimum
        self.exclusiveMinimum = exclusiveMinimum

    def schema(self, method: str) -> dict:
        retval = dict(super().schema(method))  # Important: makes a shallow copy.
        retval['type'] = 'number'
        for k in {'multipleOf', 'maximum', 'exclusiveMaximum', 'minimum', 'exclusiveMinimum'}:
            v = getattr(self, k)
            if v is not None:
                assert isinstance(v, int)
                retval[k] = v
        return retval

    def full_text_search_representation(self, data: T.Any):
        return str(data) if isinstance(data, int) else None

    def canonicalize(self, value: T.Optional[str]):
        value = super().canonicalize(value)
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            retval = int(value.strip())
            if len(str(retval)) != len(value):
                raise ValueError("{}: not an integer".format(value))
            return retval
        raise TypeError("{}: not an integer".format(value))


DISTRIBUTION = Object()
DISTRIBUTION.add('dct:title', String())
DISTRIBUTION.add('dct:description', String())
DISTRIBUTION.add('dct:issued', Date())
DISTRIBUTION.add('dct:modified', Date())
DISTRIBUTION.add('dct:license', String())
DISTRIBUTION.add('dct:rights', String())
DISTRIBUTION.add('dcat:accessURL', String(format='uri'))
DISTRIBUTION.add('dcat:downloadURL', String(format='uri'))
DISTRIBUTION.add('dcat:mediaType', String(pattern=r'^[-\w.]+/[-\w.]+$'))
DISTRIBUTION.add('dct:format', String())
DISTRIBUTION.add('dcat:byteSize', Integer(minimum=0))


VCARD = Object()
VCARD.add('vcard:fn', PlainTextLine(required='unknown'))


FOAF_AGENT = Object()
FOAF_AGENT.add('foaf:name', PlainTextLine(required='unknown'))


DATASET = Object()
DATASET.add('dct:title', String())
DATASET.add('dct:description', String())
DATASET.add('dct:issued', Date())
DATASET.add('dct:modified', Date())
DATASET.add('dct:identifier', PlainTextLine())
DATASET.add('dcat:keyword', List(PlainTextLine()))
DATASET.add('dct:language', Language())
DATASET.add('dcat:contactPoint', VCARD)
DATASET.add('dct:Temporal', String())
DATASET.add('dct:Spatial', String())
DATASET.add('dct:accrualPeriodicity', String())
DATASET.add('dcat:landingPage', String(format='uri'))
DATASET.add('dcat:theme', String(format='uri'))
DATASET.add('dct:publisher', FOAF_AGENT)
DATASET.add('dcat:distribution', DISTRIBUTION)


# import json
# print(json.dumps(
#     DATASET.schema,
#     indent='  ', sort_keys=True
# ))
