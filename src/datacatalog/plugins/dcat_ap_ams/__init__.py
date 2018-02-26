# import typing as T

from aiopluggy import HookimplMarker

from . import context, types

hookimpl = HookimplMarker('datacatalog')

_SCHEMA = 'dcat-ap-ams'


@hookimpl
def initialize_sync(app):
    types._APP = app


@hookimpl
def mds_name():
    return _SCHEMA


@hookimpl
def mds_canonicalize(data: dict) -> dict:
    return context.compact(data)


@hookimpl
def mds_json_schema() -> dict:
    return types.DATASET.schema


@hookimpl
def mds_full_text_search_representation(data: dict) -> str:
    return types.DATASET.full_text_search_representation(data)
