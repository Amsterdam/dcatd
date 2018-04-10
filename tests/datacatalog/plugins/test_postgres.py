"""Tests for the Postgres storage and search plugin.
"""
import asyncio
import base64
import copy

import aiopluggy
import collections
import os
from os import path
import pytest

from datacatalog import config, plugin_interfaces
from datacatalog.plugins import postgres as postgres_plugin

# set the config file location
os.environ['CONFIG_PATH'] = os.path.dirname(os.path.abspath(__file__)) + path.sep + 'test_postgres_config.yml'


_corpus = {
    'dutch_dataset1': {
        'doc': {'id': 'dutch_dataset1'},
        'searchable_text': 'dit is de eerste nederlandse dataset',
        'iso_639_1_code': 'nl'
    },
    'dutch_dataset2': {
        'doc': {'id': 'dutch_dataset2'},
        'searchable_text': 'dit is de tweede nederlandse dataset',
        'iso_639_1_code': 'nl'
    },
    'english_dataset1': {
        'doc': {'id': 'english_dataset1'},
        'searchable_text': 'this is the first english dataset',
        'iso_639_1_code': 'en'
    },
    'english_dataset2': {
        'doc': {'id': 'english_dataset2'},
        'searchable_text': 'this is the second english dataset',
        'iso_639_1_code': 'en'
    },
    'unspecified_language_dataset1': {
        'doc': {'id': 'unspecified_language_dataset1'},
        'searchable_text': 'isto pode ser escrito em qualquer idioma',
        'iso_639_1_code': None
    },
}

class TestApp(dict):
    def __init__(self, pool, loop, config):
        self.pool = pool
        self.loop = loop
        self.config = config


@pytest.yield_fixture(scope='module')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module', autouse=True)
def initialize(event_loop, app):
    event_loop.run_until_complete(postgres_plugin.initialize(app))


@pytest.fixture(scope='module', autouse=True)
def app():
    return TestApp(pool=None, loop=event_loop, config=config.load())


@pytest.yield_fixture(scope='function')
def corpus(event_loop, app):
    """This fixture creates the corpus for a single test and deletes it afterwards"""
    c = {}
    for doc_id, record in _corpus.items():
        c[doc_id] = copy.deepcopy(record)
        c[doc_id]['etag'] = event_loop.run_until_complete(
            postgres_plugin.storage_create(app, doc_id, **record)
        )
    try:
        yield c
    finally:
        # try to delete the corpus on exit
        for doc_id, record in c.items():
            try:
                event_loop.run_until_complete(
                    postgres_plugin.storage_delete(app=app, docid=doc_id, etags={record['etag']})
                )
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


def test_health_check(event_loop, app):
    assert event_loop.run_until_complete(postgres_plugin.health_check(app=app)) is None


def test_storage_create(corpus):
    # if the corpus fixture includes all doc ids from _corpus and has etags,
    # then uploading works.
    assert len(corpus) == len(_corpus)
    for doc_id, record in corpus.items():
        assert doc_id in corpus
        assert record['etag'] is not None


def test_storage_retrieve_no_etag(event_loop, corpus, app):
    for doc_id, record in corpus.items():
        doc, etag = event_loop.run_until_complete(
            postgres_plugin.storage_retrieve(app=app, docid=doc_id)
        )
        assert doc == record['doc']
        assert etag == record['etag']


def test_storage_retrieve_with_current_etag(event_loop, corpus, app):
    for doc_id, record in corpus.items():
        doc, etag = event_loop.run_until_complete(postgres_plugin.storage_retrieve(
            app=app, docid=doc_id, etags={record['etag']}))
        assert doc == None
        assert etag == record['etag']


def test_storage_retrieve_with_old_etag(event_loop, corpus, app):
    for doc_id, record in corpus.items():
        doc, etag = event_loop.run_until_complete(postgres_plugin.storage_retrieve(
            app=app, docid=doc_id, etags={'oldetag'}))
        assert doc == record['doc']
        assert etag == record['etag']


def test_storage_extract(event_loop, corpus, app):
    # test ids
    async def retrieve_ids():
        return [doc_id async for doc_id in postgres_plugin.storage_extract('/properties/id')]
    ids = event_loop.run_until_complete(retrieve_ids())
    assert len(ids) == len(corpus)
    assert len(set(corpus.keys()) - set(ids)) == 0
    # test nonexisting
    async def retrieve_nothing():
        return [doc_id async for doc_id in postgres_plugin.storage_extract(app=app, ptr='/items')]
    empty = event_loop.run_until_complete(retrieve_nothing())
    assert len(empty) == 0


def test_search_search(event_loop, corpus, app):
    # search on query
    async def search(record):
        q = record['searchable_text']
        return [r async for r in postgres_plugin.search_search(
            app=app, q=q, limit=1, offset=None, filters=None,
            iso_639_1_code=record['iso_639_1_code'])]
    for doc_id, record in corpus.items():
        for docid, doc in event_loop.run_until_complete(search(record)):
            assert doc == record['doc']
            assert docid == doc_id
    # filtered search
    async def search(record):
        filters = {'/properties/id': {'eq': record['doc']['id']}}
        return [r async for r in postgres_plugin.search_search(
            app=app, q='', limit=1, offset=None, filters=filters,
            iso_639_1_code=record['iso_639_1_code'])]
    for doc_id, record in corpus.items():
        for docid, doc in event_loop.run_until_complete(search(record)):
            assert doc == record['doc']
            assert docid == doc_id


def test_storage_delete(event_loop, corpus, app):
    for doc_id, record in corpus.items():
        event_loop.run_until_complete(
            postgres_plugin.storage_delete(
                app=app, docid=doc_id, etags={record['etag']})
        )
