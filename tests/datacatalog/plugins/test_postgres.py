"""Tests for the Postgres storage and search plugin.
"""
import asyncio
import base64
import copy
import os
from os import path

import aiopluggy
import pytest

from datacatalog import config, plugin_interfaces
from datacatalog.plugins import postgres as postgres_plugin

# set the config file location
os.environ['CONFIG_PATH'] = os.path.dirname(
    os.path.abspath(__file__)) + path.sep + 'test_postgres_config.yml'

_corpus = {
    'dutch_dataset1': {
        'doc': {
            'id': 'dutch_dataset1',
            'keywords': ['foo', 'bar']
        },
        'searchable_text': {'A': 'Nederlands 1', 'B': '', 'C': 'dit is de eerste nederlandse dataset', 'D': ''},
        'iso_639_1_code': 'nl'
    },
    'dutch_dataset2': {
        'doc': {
            'id': 'dutch_dataset2',
            'keywords': ['foo', 'baz']
        },
        'searchable_text': {'A': 'Nederlands 2', 'B': '', 'C': 'dit is de tweede nederlandse dataset', 'D': ''},
        'iso_639_1_code': 'nl'
    },
    'english_dataset1': {
        'doc': {'id': 'english_dataset1'},
        'searchable_text':  {'A': 'English 1', 'B': '', 'C': 'this is the first english dataset', 'D': ''},
        'iso_639_1_code': 'en'
    },
    'english_dataset2': {
        'doc': {'id': 'english_dataset2'},
        'searchable_text': {'A': 'English 2', 'B': '', 'C': 'this is the second english dataset', 'D': ''},
        'iso_639_1_code': 'en'
    },
    'unspecified_language_dataset1': {
        'doc': {'id': 'unspecified_language_dataset1'},
        'searchable_text': {'A': 'Unspecified', 'B': '', 'C': 'isto pode ser escrito em qualquer idioma', 'D': ''},
        'iso_639_1_code': None
    },
}


class MockApp(dict):
    def __init__(self, loop, config):
        super().__init__()
        self.loop = loop
        self.config = config
        loop.run_until_complete(postgres_plugin.initialize(self))


@pytest.yield_fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module', autouse=True)
def initialize(event_loop, app):
    event_loop.run_until_complete(postgres_plugin.initialize(app))


@pytest.fixture(scope='module', autouse=True)
def app(event_loop):
    return MockApp(loop=event_loop, config=config.load())


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
                    postgres_plugin.storage_delete(app=app, docid=doc_id,
                                                   etags={record['etag']})
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
    assert event_loop.run_until_complete(
        postgres_plugin.health_check(app=app)) is None


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
        doc, etag = event_loop.run_until_complete(
            postgres_plugin.storage_retrieve(
                app=app, docid=doc_id, etags={record['etag']}))
        assert doc == None
        assert etag == record['etag']


def test_storage_retrieve_with_old_etag(event_loop, corpus, app):
    for doc_id, record in corpus.items():
        doc, etag = event_loop.run_until_complete(
            postgres_plugin.storage_retrieve(
                app=app, docid=doc_id, etags={'oldetag'}))
        assert doc == record['doc']
        assert etag == record['etag']


def test_storage_extract(event_loop, corpus, app):
    # test ids
    async def retrieve_ids():
        return [doc_id async for doc_id in
                postgres_plugin.storage_extract(app, '/properties/id')]

    ids = event_loop.run_until_complete(retrieve_ids())
    assert len(ids) == len(corpus)
    assert len(set(corpus.keys()) - set(ids)) == 0

    # test nonexisting
    async def retrieve_nothing():
        return [doc_id async for doc_id in
                postgres_plugin.storage_extract(app=app, ptr='/items')]

    empty = event_loop.run_until_complete(retrieve_nothing())
    assert len(empty) == 0


def test_search_search(event_loop, corpus, app):
    # search on query
    async def search(record):
        q = record['searchable_text']['C']
        return [r async for r in postgres_plugin.search_search(
            app=app, q=q, sortpath=['@id'], result_info={}, limit=1,
            filters=None, iso_639_1_code=record['iso_639_1_code'])]

    for corpus_id, corpus_doc in corpus.items():
        for docid, doc in event_loop.run_until_complete(search(corpus_doc)):
            assert doc == corpus_doc['doc']
            assert docid == corpus_id

    # filtered search on object property:
    async def search(record):
        filters = {'/properties/id': {'eq': record['doc']['id']}}
        return [r async for r in postgres_plugin.search_search(
            app=app, q='', sortpath=['@id'], result_info={},
            limit=1, filters=filters,
            iso_639_1_code=record['iso_639_1_code'])]

    for corpus_id, corpus_doc in corpus.items():
        results = event_loop.run_until_complete(search(corpus_doc))
        for docid, doc in results:
            assert doc == corpus_doc['doc']
            assert docid == corpus_id

    # filtered search on array item:
    async def search():
        filters = {'/properties/keywords/items': {'eq': 'foo'}}
        result_info = {}
        return [r async for r in postgres_plugin.search_search(
            app=app, q='', sortpath=['@id'], result_info=result_info,
            facets=['/properties/keywords/items'],
            limit=1, filters=filters,
            iso_639_1_code='nl')], result_info

    results, result_info = event_loop.run_until_complete(search())
    assert result_info == {
        '/': 2,
        '/properties/keywords/items': {'foo': 2, 'bar': 1, 'baz': 1}
    }
    assert len(results) == 1
    assert results[0][0] == 'dutch_dataset1'


def test_storage_delete(event_loop, corpus, app):
    for doc_id, record in corpus.items():
        event_loop.run_until_complete(
            postgres_plugin.storage_delete(
                app=app, docid=doc_id, etags={record['etag']})
        )


def test_to_pg_json_query():
    assert postgres_plugin._to_pg_json_query("Veer 1") == "Veer:* & 1:*"
    assert postgres_plugin._to_pg_json_query_fullmatch("s") == "s"
    assert postgres_plugin._to_pg_json_query("s-Gravelandse Veer 1") == "s-Gravelandse:* & Veer:* & 1:*"
