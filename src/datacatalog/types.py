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
