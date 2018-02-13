import typing as T

from aiopluggy import HookimplMarker

from . import context, types

hookimpl = HookimplMarker('datacatalog')

_SCHEMA = 'dcat-ap-ams'

@hookimpl
def initialize_sync(app):
    pass


@hookimpl
async def initialize(app):
    pass


@hookimpl
def mds_name():
    return _SCHEMA


@hookimpl
def normalize(schema: str, data: dict) -> T.Optional[dict]:
    if schema != _SCHEMA:
        return None
    return context.compact(data)


@hookimpl
def mds_json_schema(schema_name: str) -> T.Optional[dict]:
    if schema_name != _SCHEMA:
        return None
    return types.DATASET.schema
