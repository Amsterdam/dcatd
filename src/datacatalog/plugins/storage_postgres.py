"""Postgres storage plugin.
"""
import base64
import hashlib
import json
import logging
import pkg_resources
import secrets
import typing as T
import yaml

import aiopluggy
import asyncpg.pool

_pool: asyncpg.pool.Pool = None
_hookimpl = aiopluggy.HookimplMarker('datacatalog')
_logger = logging.getLogger('plugin.storage.postgres')

_Q_HEALTHCHECK = 'SELECT 1'
_Q_RETRIEVE_DOC = 'SELECT doc FROM Dataset WHERE id = $1'
_Q_RETRIEVE_IDS = 'SELECT id FROM Dataset'
_Q_INSERT_DOC = 'INSERT INTO Dataset VALUES ($1, $2, to_tsvector($3, $4), $5)'
_Q_UPDATE_DOC = 'UPDATE Dataset SET doc=$1, searchable_text=to_tsvector($2, $3), etag=$4 WHERE id=$5 AND etag=$6 RETURNING id'
_Q_DELETE_DOC = 'DELETE FROM Dataset WHERE id=$1 AND etag=$2 RETURNING id'


@_hookimpl
async def initialize(app):
    # language=rst
    """ Initialize the plugin.

    This function validates the configuration and creates a connection pool.
    The pool is stored as a module-scoped singleton in _pool.

    """
    global _pool

    if _pool is not None:
        # Not failing hard because not sure whether initializing twice is allowed
        _logger.warning("plugin is already intialized, refusing to initialize again")
        return

    # validate configuration
    with pkg_resources.resource_stream(__name__, 'storage_postgres_config_schema.yml') as s:
        schema = yaml.load(s)
    app.config.validate(schema)

    # create asyncpg engine
    dbconf = app.config['storage_postgres']
    _logger.info("Connecting to database: postgres://%s:%i/%s",
                 dbconf['host'], dbconf['port'], dbconf['name'])
    _pool = await asyncpg.create_pool(
        user=dbconf['user'],
        database=dbconf['name'],
        host=dbconf['host'],
        port=dbconf['port'],
        password=dbconf['pass']
    )


@_hookimpl
async def health_check() -> T.Optional[str]:
    # language=rst
    """ Health check.

    :returns: If unhealthy, a string describing the problem, otherwise ``None``.
    :raises Exception: if that's easier than returning a string.

    """
    if (await _pool.fetchval(_Q_HEALTHCHECK)) != 1:
        return 'Postgres connection problem'
    return None


@_hookimpl
async def storage_retrieve(id: str) -> dict:
    # language=rst
    """ Get document by id.

    :returns: a "JSON dictionary"
    :raises KeyError: if not found

    """
    doc = await _pool.fetchval(_Q_RETRIEVE_DOC, id)
    if doc is None:
        raise KeyError()
    return json.loads(doc)


@_hookimpl
async def storage_retrieve_ids() -> T.Generator[int, None, None]:
    # language=rst
    """ Get a list containing all document identifiers.
    """
    async with _pool.acquire() as con:
        # use a cursor so we can stream
        async for row in con.cursor(_Q_RETRIEVE_IDS):
            yield row['id']


@_hookimpl
async def storage_store(id: str, doc: dict, searchable_text: str, doc_language: str, etag: T.Optional[str]) -> str:
    # language=rst
    """ Store document.

    :param id: the ID under which to store this document. May or may not
        already exist in the data store.
    :param doc: the document to store; a "JSON dictionary".
    :param searchable_text: this will be indexed for free-text search.
    :param doc_language: the language of the document. Will be used for free-text search indexing.
    :param etag: the last known ETag of this document, or ``None`` if no
        document with this ``id`` should exist yet.
    :returns: new ETag
    :raises: ValueError if the given etag doesn't match the stored etag, or if
             no etag is given while the doc identifier already exists.

    """
    new_doc = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    # the etag is a hash of the document
    hash = hashlib.sha3_224()
    hash.update(new_doc.encode())
    new_etag = '"' + base64.urlsafe_b64encode(hash.digest()).decode() + '"'
    if etag is None:
        try:
            await _pool.execute(_Q_INSERT_DOC, id, new_doc, searchable_text, doc_language, new_etag)
        except asyncpg.exceptions.UniqueViolationError:
            _logger.debug('Document {} exists but no etag provided'.format(id))
            raise ValueError
    elif (await _pool.fetchval(_Q_UPDATE_DOC, new_doc, searchable_text, doc_language, new_etag, id, etag)) is None:
            raise ValueError
    return new_etag


@_hookimpl
async def storage_id() -> str:
    # language=rst
    """New unique identifier.

    Returns a URL-safe random token with 80 bits of entropy, base64 encoded in
    ~13 characters. Given the birthday paradox this should be safe upto about
    10 bilion (2^35) entries, when the probability of collisions is
    approximately 0.05% (p=0.0005).

    """
    return secrets.token_urlsafe(nbytes=10)


@_hookimpl
async def storage_delete(id: str, etag: str) -> None:
    # language=rst
    """ Delete document.

    :param id: the ID of the document to delete.
    :param etag: the last known ETag of this document.
    :raises: ValueError if the given etag doesn't match the stored etag.
    :raises: KeyError if a document with the given id doesn't exist.

    """
    if (await _pool.fetchval(_Q_DELETE_DOC, id, etag)) is None:
        # the delete may fail because either the id doesn't exist or the given
        # etag doesn't match. There's no way to atomically check for both
        # conditions at the same time, apart from a full table lock. However,
        # all scenario's in which the below, not threat-safe way of identifying
        # the cause of failure is not correct, are trivial.
        try:
            await storage_retrieve(id)
        except KeyError:
            _logger.debug('Document {} not found'.format(id))
            raise
        _logger.debug('Etag ({}) mismatch for {}'.format(etag, id))
        raise ValueError
