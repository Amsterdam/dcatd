class Type(object):
    def __init__(self, *args, title=None, description=None, required=False, **kwargs):
        if len(args) > 0 or len(kwargs) > 0:
            raise ValueError()
        self.title = title
        self.description = description
        self.required = required

    @property
    def schema(self) -> dict:
        retval = {}
        if self.title is not None:
            retval['title'] = self.title
        if self.description is not None:
            retval['title'] = self.description
        return retval


class List(Type):
    def __init__(self, item_type: Type, *args, allow_empty=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type
        self.allow_empty = allow_empty

    @property
    def schema(self) -> dict:
        retval = dict(super().schema)
        retval.update({
            'type': 'array',
            'items': self.item_type.schema
        })
        if not self.allow_empty:
            retval['minItems'] = 1
        return retval


class SomeOf(Type):
    def __init__(self, boolean, *types, **kwargs):
        assert boolean in {'allOf', 'anyOf', 'oneOf'}
        super().__init__(**kwargs)
        self.boolean = boolean
        self.types = list(types)

    @property
    def schema(self) -> dict:
        retval = dict(super().schema)
        retval[self.boolean] = [v.schema for v in self.types]
        return retval


class Object(Type):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.properties = []
        self.last = None

    @property
    def property_names(self):
        return [x[0] for x in self.properties]

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

    @property
    def schema(self) -> dict:
        retval = dict(super().schema)
        retval.update({
            'type': 'object',
            'properties': {
                name: value.schema
                for name, value in self.properties
            }
        })
        required = [name for name, value in self.properties if value.required]
        if len(required) > 0:
            retval['required'] = required
        return retval


class String(Type):
    def __init__(self, *args,
                 pattern=None, max_length=None, format=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern = pattern
        self.max_length = max_length
        self.format = format

    @property
    def schema(self) -> dict:
        retval = dict(super().schema)
        retval['type'] = 'string'
        if self.pattern is not None:
            retval['pattern'] = self.pattern
        if self.max_length is not None:
            retval['maxLength'] = self.max_length
        if self.format is not None:
            retval['format'] = self.format
        return retval


class Enum(Type):
    def __init__(self, values, default=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.values = values
        self.default = default

    @property
    def schema(self) -> dict:
        retval = dict(super().schema)
        retval['type'] = 'string'
        retval['enum'] = [v[0] for v in self.values]
        retval['enumNames'] = [v[1] for v in self.values]
        if self.default is not None:
            retval['default'] = self.default
        return retval


class Date(String):
    def __init__(self, *args, format=None, pattern=None, **kwargs):
        assert format is None and pattern is None
        super().__init__(*args, format='date', pattern=r'^\d\d\d\d-\d\d-\d\d$', **kwargs)


class Language(String):
    def __init__(self, *args, format=None, pattern=None, **kwargs):
        assert format is None and pattern is None
        super().__init__(*args, format='lang', pattern=r'^(?:lang1:\w\w|lang2:\w\w\w)$', **kwargs)


class PlainTextLine(String):
    def __init__(self, *args, format=None, pattern=r'^[^\n\r]*?\S[^\n\r]*$', **kwargs):
        assert format is None
        super().__init__(*args, format='line', pattern=pattern, **kwargs)


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

    @property
    def schema(self) -> dict:
        retval = dict(super().schema)
        retval['type'] = 'number'
        for k in {'multipleOf', 'maximum', 'exclusiveMaximum', 'minimum', 'exclusiveMinimum'}:
            v = getattr(self, k)
            if v is not None:
                assert isinstance(v, int)
                retval[k] = v
        return retval


DISTRIBUTION = Object()
DISTRIBUTION.add('dct:title', String())
DISTRIBUTION.add('dct:description', String())
DISTRIBUTION.add('dct:issued', Date())
DISTRIBUTION.add('dct:modified', Date())
DISTRIBUTION.add('dct:license', String())
DISTRIBUTION.add('dct:rights', String())
DISTRIBUTION.add('dcat:accessURL', String(format='uri'))
DISTRIBUTION.add('dcat:downloadURL', String(format='uri'))
DISTRIBUTION.add('dcat:mediaType', PlainTextLine(pattern=r'^[-\w.]+/[-\w.]+$'))
DISTRIBUTION.add('dct:format', String())
DISTRIBUTION.add('dcat:byteSize', Integer(minimum=0))


VCARD = Object()
VCARD.add('vcard:fn', PlainTextLine(required=True))


FOAF_AGENT = Object()
FOAF_AGENT.add('foaf:name', PlainTextLine(required=True))


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
