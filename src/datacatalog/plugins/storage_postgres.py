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

import aiohttp.web
import aiopluggy
import asyncpg.pool

_pool: asyncpg.pool.Pool = None
_hookimpl = aiopluggy.HookimplMarker('datacatalog')
_logger = logging.getLogger('plugin.storage.postgres')

_Q_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS documents(
        id CHARACTER VARYING(254) PRIMARY KEY,
        doc JSONB NOT NULL,
        etag CHARACTER VARYING(254) NOT NULL
    );
    CREATE INDEX ON documents (id, etag);
"""
_Q_HEALTHCHECK = 'SELECT 1;'
_Q_RETRIEVE_DOC = 'SELECT doc FROM documents WHERE id = $1'
_Q_RETRIEVE_IDS = 'SELECT id FROM documents'
_Q_INSERT_DOC = 'INSERT INTO documents VALUES ($1, $2, $3)'
_Q_UPDATE_DOC = 'UPDATE documents SET doc=$1, etag=$2 WHERE id=$3 AND etag=$4 RETURNING id'


@_hookimpl
async def initialize(app):
    # language=rst
    """ Initialize the plugin.

    This function validates the configuration and creates a connection pool.
    The pool is stored as a module-scoped singleton in _pool. If the documents
    table doesn't exist it is created.

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

    # creaqte table
    await _pool.execute(_Q_CREATE_TABLE)


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
async def storage_store(id: str, doc: dict, etag: T.Optional[str]) -> str:
    # language=rst
    """ Store document.

    :param id: the ID under which to store this document. May or may not
        already exist in the data store.
    :param doc: the document to store; a "JSON dictionary".
    :param etag: the last known ETag of this document, or ``None`` if no
        document with this ``id`` should exist yet.
    :returns: new ETag
    :raises: aiohttp.web.HTTPPreconditionFailed
    :raises: aiohttp.web.HTTPNotFound

    """
    new_doc = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    # the etag is a hash of the document
    hash = hashlib.sha3_224()
    hash.update(new_doc.encode())
    new_etag = '"' + base64.urlsafe_b64encode(hash.digest()).decode() + '"'
    if etag is None:
        try:
            await _pool.execute(_Q_INSERT_DOC, id, new_doc, new_etag)
        except asyncpg.exceptions.UniqueViolationError:
            raise aiohttp.web.HTTPExpectationFailed()
    else:
        if (await _pool.fetchval(_Q_UPDATE_DOC, new_doc, new_etag, id, etag)) is None:
            # there's no nice way to see whether an UPDATE failed. I'm using
            # the RETURNING clause. If the returned value is None, the doc
            # isn't updated. We then check if a doc with the same ID exists. If
            # it doesn't then we raise a 404, otherwise 412. This isn't atomic
            # but we don't need to be completely correct in reporting the
            # error - in a world of fast concurrent inserts, updates and
            # deletes results may be outdated before they're communicated
            # anyway. This way we stay lock free at least.
            try:
                await storage_retrieve(id)
            except KeyError:
                raise aiohttp.web.HTTPNotFound()
            raise aiohttp.web.HTTPExpectationFailed
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
