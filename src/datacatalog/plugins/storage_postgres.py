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

_q_retrieve_doc = 'SELECT doc FROM documents WHERE id = $1'
_q_retrieve_ids = 'SELECT id FROM documents'
_q_insert_doc = 'INSERT INTO documents VALUES ($1, $2, $3)'
_q_update_doc = 'UPDATE documents SET doc=$1, etag=$2 WHERE id=$3 AND etag=$4) RETURNING id'


@_hookimpl
async def initialize(app):
    # language=rst
    """ Initialize the plugin.

    This function validates the configuration and creates a connection pool.
    The pool is stored as a module-scoped singleton in _pool.

    """
    nonlocal _pool

    if _pool is not None:
        # Not failing hard because not sure whether initializing twice is allowed
        _logger.warning("plugin is already intialized, refusing to initialize again")
        return

    # validate configuration
    with pkg_resources.resource_stream(__name__, 'storage_postgres_config_schema.yml') as s:
        schema = yaml.load(s)
    app.config.validate(schema)

    # create asyncpg engine
    dbconf = app.config['postgres_storage_plugin']
    _logger.info("Connecting to database: postgres://%s:%i/%s",
                 dbconf['host'], dbconf['port'], dbconf['dbname'])
    _pool = await asyncpg.create_pool(
        user=dbconf['user'],
        database=dbconf['dbname'],
        host=dbconf['host'],
        port=dbconf['port'],
        password=dbconf['password']
    )


@_hookimpl
async def storage_retrieve(id: str) -> dict:
    # language=rst
    """ Get document by id.

    :returns: a "JSON dictionary"
    :raises KeyError: if not found

    """
    doc = await _pool.fetchval(_q_retrieve_doc, id)
    if doc is None:
        raise KeyError()
    return json.loads(doc)


@_hookimpl
async def storage_retrieve_ids() -> T.Generator[int]:
    # language=rst
    """ Get a list containing all document identifiers.
    """
    async with _pool.acquire() as con:
        # use a cursor so we can stream
        async for row in con.cursor(_q_retrieve_ids):
            yield row['id']


@_hookimpl
async def storage_store(id: str, doc: dict, etag: T.Optional[str]=None) -> str:
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
    hash = hashlib.sha3_224()
    hash.update(new_doc.encode())
    new_etag = '"' + base64.urlsafe_b64encode(hash.digest()).decode() + '"'
    if etag is None:
        try:
            await _pool.execute(_q_insert_doc, id, new_doc, new_etag)
        except asyncpg.exceptions.UniqueViolationError:
            raise aiohttp.web.HTTPExpectationFailed()
    else:
        if (await _pool.fetchval(_q_update_doc, new_doc, new_etag, id, etag)) is None:
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
