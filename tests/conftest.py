import string
import random
import collections

import pytest

from datacatalog.app import get_app
from datacatalog.action_api import Facet

PackageInfo = collections.namedtuple('PackageInfo', field_names=('id', 'name'))
_PACKAGES = [
    PackageInfo(
        id='62513382-3b26-4bc8-9096-40b6ce8383c0',
        name="100-validated-species-of-plants"
    ),
    PackageInfo(
        id='17be64bb-da74-4195-9bb8-565c39846af2',
        name="2016-regione-asia-est-oceania-classi-di-eta"
    ),
    PackageInfo(
        id='9c3036b8-f6ac-4a4e-9036-5a3cc90c3900',
        name="1617in10-regulation-of-sale-of-overseas-properties-20170426-c"
    ),
]


@pytest.fixture(params=_PACKAGES, ids=lambda x: x.id[:8] + '...')
def package(request) -> PackageInfo:
    return request.param


@pytest.fixture()
def all_packages():
    return _PACKAGES


@pytest.fixture()
def random_string(length=None):
    if length is None:
        length = random.randint(8, 16)
    return ''.join(
        random.SystemRandom().choice(string.ascii_lowercase) for _ in range(length)
    )


####
#
# For action API
#
####

@pytest.fixture(params=range(5))
def random_facets():
    """
    FACET FIELDS should contain a json-encoded list of selected facets
    """
    facets = []
    for facet in Facet:
        if random.randint(0, 1) == 1:
            facets.append(facet.value)
    return facets


@pytest.fixture()
def random_facet_query():
    """
    FACET QUERY should contain a collection of key-value pairs where the key is
    a facet and the value the queried value for that facet. keys are plaintext,
    values are quoted, key-value pairs are seperated by spaces
    """
    facet_query = {}
    for facet in Facet:
        if random.randint(0, 1) == 1:
            facet_query[facet.value] = random_string()
    querystring = ' '.join(
        f'{k}:"{v}"' for k, v in facet_query.items()
    )
    return facet_query, querystring


@pytest.fixture()
def dcat_client(loop, test_client):
    return loop.run_until_complete(test_client(get_app()))
