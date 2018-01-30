import asyncio
import base64
import collections
import os.path

import aiopluggy
import pytest

from datacatalog import config, plugin_interfaces
from datacatalog.plugins import postgres as postgres_plugin

# set the config file location
os.environ['CONFIG_PATH'] = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'test_postgres_config.yml'


corpus = {
    'dutch_dataset1': {
        'doc': {'id': 'dutch_dataset1'},
        'searchable_text': 'dit is de eerste nederlandse dataset',
        'iso_639_1_code': 'nl',
        'etag': None
    },
    'dutch_dataset2': {
        'doc': {'id': 'dutch_dataset2'},
        'searchable_text': 'dit is de tweede nederlandse dataset',
        'iso_639_1_code': 'nl',
        'etag': None
    },
    'english_dataset1': {
        'doc': {'id': 'english_dataset1'},
        'searchable_text': 'this is the first english dataset',
        'iso_639_1_code': 'en',
        'etag': None
    },
    'english_dataset2': {
        'doc': {'id': 'english_dataset2'},
        'searchable_text': 'this is the second english dataset',
        'iso_639_1_code': 'en',
        'etag': None
    },
    'unspecified_language_dataset1': {
        'doc': {'id': 'unspecified_language_dataset1'},
        'searchable_text': 'isto pode ser escrito em qualquer idioma',
        'iso_639_1_code': None,
        'etag': None
    },
}

cache = set()


@pytest.yield_fixture(scope='module')
def event_loop():
    loop = asyncio.get_event_loop()
    try:
        yield loop
    except:
        # we do this so we can cleanup. note that any exception will be reraised anyway.
        pass
    # try to delete the corpus on exit
    for doc_id in cache:
        record = corpus[doc_id]
        try:
            loop.run_until_complete(postgres_plugin.storage_delete(doc_id, record['etag']))
        except:
            pass
    loop.close()


@pytest.fixture(scope='module', autouse=True)
def initialize(event_loop):
    App = collections.namedtuple('Application', 'config loop')
    app = App(config.load(), event_loop)
    event_loop.run_until_complete(postgres_plugin.initialize(app))


def test_storage_id(event_loop):
    id = event_loop.run_until_complete(postgres_plugin.storage_id())
    id += '=' * (4 - (len(id) % 4))  # secrets.token_urlsafe strips the padding
    assert len(base64.urlsafe_b64decode(id)) == 10


def test_signatures():
    pm = aiopluggy.PluginManager('datacatalog')
    pm.register_specs(plugin_interfaces)
    pm.register(postgres_plugin)


def test_health_check(event_loop):
    assert event_loop.run_until_complete(postgres_plugin.health_check()) is None


def test_storage_store(event_loop):
    for doc_id, record in corpus.items():
        record['etag'] = event_loop.run_until_complete(
            postgres_plugin.storage_store(doc_id, **record)
        )
        cache.add(doc_id)


def test_storage_retrieve(event_loop):
    for doc_id in cache:
        doc, etag = event_loop.run_until_complete(postgres_plugin.storage_retrieve(doc_id))
        record = corpus[doc_id]
        assert doc == record['doc']
        assert etag == record['etag']


def test_storage_retrieve_ids(event_loop):
    async def retrieve_ids():
        return [doc_id async for doc_id in postgres_plugin.storage_retrieve_ids()]
    ids = event_loop.run_until_complete(retrieve_ids())
    for doc_id in ids:
        assert doc_id in cache


@pytest.mark.xfail
def test_search_search(event_loop):
    async def search_records(record):
        q = record['searchable_text']
        return [r async for r in postgres_plugin.search_search(q, 1, None, record['iso_639_1_code'])]
    for doc_id in cache:
        for doc, etag in event_loop.run_until_complete(search_records(corpus[doc_id])):
            assert doc['id'] == doc_id
            assert etag == corpus[doc_id]['etag']



def test_storage_delete(event_loop):
    for doc_id in cache:
        record = corpus[doc_id]
        event_loop.run_until_complete(postgres_plugin.storage_delete(doc_id, record['etag']))
