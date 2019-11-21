from pkg_resources import resource_stream

import yaml


_OPENAPI_SCHEMA_RESOURCE = 'openapi.yml'

with resource_stream(__name__, _OPENAPI_SCHEMA_RESOURCE) as s:
    openapi = yaml.safe_load(s)
