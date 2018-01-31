"""Tests for the Postgres storage and search plugin.
"""
import asyncio
import base64
import collections
import copy
import json
import os.path

import aiopluggy
import pytest

from datacatalog import config, plugin_interfaces
from datacatalog.plugins import postgres as postgres_plugin

# set the config file location
os.environ['CONFIG_PATH'] = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'test_postgres_config.yml'


_corpus = {
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


@pytest.yield_fixture(scope='module')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module', autouse=True)
def initialize(event_loop):
    App = collections.namedtuple('Application', 'config loop')
    app = App(config.load(), event_loop)
    event_loop.run_until_complete(postgres_plugin.initialize(app))


@pytest.yield_fixture(scope='function')
def corpus(event_loop):
    """This fixture creates the corpus for a single test and deletes it afterwards"""
    c = {}
    for doc_id, record in _corpus.items():
        c[doc_id] = copy.deepcopy(record)
        c[doc_id]['etag'] = event_loop.run_until_complete(
            postgres_plugin.storage_store(doc_id, **record)
        )
    try:
        yield c
    finally:
        # try to delete the corpus on exit
        for doc_id, record in c.items():
            try:
                event_loop.run_until_complete(postgres_plugin.storage_delete(doc_id, record['etag']))
            except:
                pass


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


def test_storage_store(corpus):
    # if the corpus fixture includes all doc ids from _corpus and has etags,
    # then uploading works.
    assert len(corpus) == len(_corpus)
    for doc_id, record in corpus.items():
        assert doc_id in corpus
        assert record['etag'] is not None


def test_storage_retrieve(event_loop, corpus):
    for doc_id, record in corpus.items():
        doc, etag = event_loop.run_until_complete(postgres_plugin.storage_retrieve(doc_id))
        assert doc == record['doc']
        assert etag == record['etag']


def test_storage_retrieve_ids(event_loop, corpus):
    async def retrieve_ids():
        return [doc_id async for doc_id in postgres_plugin.storage_retrieve_ids()]
    ids = event_loop.run_until_complete(retrieve_ids())
    assert len(ids) == len(corpus)
    assert len(set(corpus.keys()) - set(ids)) == 0


def test_search_search(event_loop, corpus):
    async def search_records(record):
        q = record['searchable_text']
        return [r async for r in postgres_plugin.search_search(q, 1, None, record['iso_639_1_code'])]
    for doc_id, record in corpus.items():
        for doc, etag in event_loop.run_until_complete(search_records(record)):
            assert json.loads(doc) == record['doc']
            assert etag == record['etag']


def test_storage_delete(event_loop, corpus):
    for doc_id, record in corpus.items():
        event_loop.run_until_complete(postgres_plugin.storage_delete(doc_id, record['etag']))
