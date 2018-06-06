"""Postgres storage and search plugin.
"""
import asyncio
import base64
import collections
import hashlib
import json
import logging
import pkg_resources
import secrets
import typing as T
import yaml

import aiopluggy
import asyncpg.pool
import jsonpointer

from aiohttp_extras import conditional

from .languages import ISO_639_1_TO_PG_DICTIONARIES

_hookimpl = aiopluggy.HookimplMarker('datacatalog')
_logger = logging.getLogger(__name__)

CONNECT_ATTEMPT_INTERVAL_SECS = 2
CONNECT_ATTEMPT_MAX_TRIES = 5
_DEFAULT_CONNECTION_TIMEOUT = 60
_DEFAULT_MIN_POOL_SIZE = 0
_DEFAULT_MAX_POOL_SIZE = 5
_DEFAULT_MAX_INACTIVE_CONNECTION_LIFETIME = 5.0

_Q_CREATE = '''
CREATE TABLE IF NOT EXISTS "dataset" (
    "id" character varying(254) PRIMARY KEY,
    "doc" jsonb NOT NULL,
    "etag" character varying(254) NOT NULL,
    "searchable_text" tsvector,
    "lang" character varying(20)
);
CREATE INDEX IF NOT EXISTS "idx_id_etag" ON "dataset" ("id", "etag");
CREATE INDEX IF NOT EXISTS "idx_full_text_search" ON "dataset" USING gin ("searchable_text");
CREATE INDEX IF NOT EXISTS "idx_json_docs" ON "dataset" USING gin ("doc" jsonb_path_ops);
'''
_Q_HEALTHCHECK = 'SELECT 1'
_Q_RETRIEVE_DOC = 'SELECT doc, etag FROM "dataset" WHERE id = $1'
_Q_INSERT_DOC = 'INSERT INTO "dataset" (id, doc, searchable_text, lang, etag) VALUES ($1, $2, to_tsvector($3, $4), $3, $5)'
_Q_UPDATE_DOC = 'UPDATE "dataset" SET doc=$1, searchable_text=to_tsvector($2, $3), lang=$2, etag=$4 WHERE id=$5 AND etag=ANY($6) RETURNING id'
_Q_DELETE_DOC = 'DELETE FROM "dataset" WHERE id=$1 AND etag=ANY($2) RETURNING id'
_Q_RETRIEVE_ALL_DOCS = 'SELECT doc FROM "dataset"'
_Q_SEARCH_DOCS = """
SELECT id, doc, ts_rank_cd(searchable_text, query) AS rank
FROM "dataset", to_tsquery($1, $2) query
WHERE (''=$2::varchar OR searchable_text @@ query) {filters}
AND ('simple'=$1::varchar OR lang=$1::varchar)
ORDER BY rank DESC;
"""
_Q_LIST_DOCS = """
SELECT id, doc
FROM "dataset"
WHERE ('simple'=$1::varchar OR lang=$1::varchar) {filters}
ORDER BY {sortexpression} DESC;
"""


@_hookimpl
async def initialize(app):
    # language=rst
    """ Initialize the plugin.

    This function validates the configuration and creates a connection pool.
    The pool is stored as a module-scoped singleton in app['pool'].

    """

    if app.get('pool') is not None:
        # Not failing hard because not sure whether initializing twice is allowed
        _logger.warning("Plugin is already intialized. Deinitializing before proceeding.")
        await deinitialize(app)

    # validate configuration
    with pkg_resources.resource_stream(__name__, 'config_schema.yml') as s:
        schema = yaml.load(s)
    app.config.validate(schema)
    dbconf = app.config['storage_postgres']

    # check for optional config
    conn_timeout = dbconf.get('connection_timeout', _DEFAULT_CONNECTION_TIMEOUT)
    min_pool_size = dbconf.get('min_pool_size', _DEFAULT_MIN_POOL_SIZE)
    max_pool_size = dbconf.get('max_pool_size', _DEFAULT_MAX_POOL_SIZE)
    max_inactive_conn_lifetime = dbconf.get(
        'max_inactive_connection_lifetime', _DEFAULT_MAX_INACTIVE_CONNECTION_LIFETIME)

    # create asyncpg engine
    _logger.info("Connecting to database: postgres://%s:%i/%s",
                 dbconf['host'], dbconf['port'], dbconf['name'])

    connect_attempt_tries_left = CONNECT_ATTEMPT_MAX_TRIES - 1
    while connect_attempt_tries_left >= 0:
        try:
            app['pool'] = await asyncpg.create_pool(
                user=dbconf['user'],
                database=dbconf['name'],
                host=dbconf['host'],
                port=dbconf['port'],
                password=dbconf['pass'],
                timeout=conn_timeout,
                min_size=min_pool_size,
                max_size=max_pool_size,
                max_inactive_connection_lifetime=max_inactive_conn_lifetime,
                loop=app.loop
            )
        except ConnectionRefusedError:
            if connect_attempt_tries_left > 0:
                _logger.warning("Database not accepting connections. Retrying %d more times.", connect_attempt_tries_left)
                connect_attempt_tries_left -= 1
                await asyncio.sleep(CONNECT_ATTEMPT_INTERVAL_SECS)
            else:
                _logger.error("Could not connect to the database. Aborting.")
                raise
        else:
            break
    while connect_attempt_tries_left >= 0:
        try:
            await app['pool'].execute(_Q_CREATE)
        except ConnectionRefusedError:
            if connect_attempt_tries_left > 0:
                _logger.warning("Database not accepting connections. Retrying %d more times.", connect_attempt_tries_left)
                connect_attempt_tries_left -= 1
                await asyncio.sleep(CONNECT_ATTEMPT_INTERVAL_SECS)
            else:
                _logger.error("Could not connect to the database. Aborting.")
                raise
        else:
            break
    _logger.info("Successfully connected to postgres.")


@_hookimpl
async def deinitialize(app):
    # language=rst
    """ Deinitialize the plugin."""
    await app['pool'].close()
    del app['pool']


@_hookimpl
async def health_check(app) -> T.Optional[str]:
    # language=rst
    """ Health check.

    :returns: If unhealthy, a string describing the problem, otherwise ``None``.
    :raises Exception: if that's easier than returning a string.

    """
    if (await app['pool'].fetchval(_Q_HEALTHCHECK)) != 1:
        return 'Postgres connection problem'


@_hookimpl
async def storage_retrieve(app: T.Mapping, docid: str, etags: T.Optional[T.Set[str]] = None) \
        -> T.Tuple[T.Optional[dict], str]:
    # language=rst
    """ Get document and corresponsing etag by id.

    :param docid: document id
    :param etags: None, or a set of Etags
    :returns:
        A tuple. The first element is either the document or None if the
        document's Etag corresponds to one of the given etags. The second
        element is the current etag.
    :raises KeyError: if not found

    """
    record = await app['pool'].fetchrow(_Q_RETRIEVE_DOC, docid)
    if record is None:
        raise KeyError()
    if etags and conditional.match_etags(record['etag'], etags, True):
        return None, record['etag']
    return json.loads(record['doc']), record['etag']


@_hookimpl
async def storage_create(app: T.Mapping, docid: str, doc: dict, searchable_text: str,
                         iso_639_1_code: T.Optional[str]) -> str:
    # language=rst
    """ Store a new document.

    :param docid: the ID under which to store this document. May or may not
        already exist in the data store.
    :param doc: the document to store; a "JSON dictionary".
    :param searchable_text: this will be indexed for free-text search.
    :param iso_639_1_code: the language of the document.
    :returns: new ETag
    :raises: KeyError if the docid already exists.
    """
    new_doc = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    new_etag = _etag_from_str(new_doc)
    lang = _iso_639_1_code_to_pg(iso_639_1_code)
    try:
        await app['pool'].execute(_Q_INSERT_DOC, docid, new_doc, lang, searchable_text, new_etag)
    except asyncpg.exceptions.UniqueViolationError as e:
        raise KeyError from e
    return new_etag


@_hookimpl
async def storage_update(app: T.Mapping, docid: str, doc: dict, searchable_text: str,
                         etags: T.Set[str], iso_639_1_code: T.Optional[str]) \
        -> str:
    # language=rst
    """ Update the document with the given ID only if it has one of the provided Etags.

    :param docid: the ID under which to store this document. May or may not
        already exist in the data store.
    :param doc: the document to store; a "JSON dictionary".
    :param searchable_text: this will be indexed for free-text search.
    :param etags: one or more Etags.
    :param iso_639_1_code: the language of the document.
    :returns: new ETag
    :raises: ValueError if none of the given etags match the stored etag.
    :raises: KeyError if the docid doesn't exist.
    """
    new_doc = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    new_etag = _etag_from_str(new_doc)
    lang = _iso_639_1_code_to_pg(iso_639_1_code)
    if (await app['pool'].fetchval(_Q_UPDATE_DOC, new_doc, lang, searchable_text, new_etag, docid, list(etags))) is None:
        raise ValueError
    return new_etag


@_hookimpl
async def storage_delete(app: T.Mapping, docid: str, etags: T.Set[str]) -> None:
    # language=rst
    """ Delete document only if it has one of the provided Etags.

    :param docid: the ID of the document to delete.
    :param etags: the last known ETags of this document.
    :raises: ValueError if none of the given etags match the stored etag.
    :raises: KeyError if a document with the given id doesn't exist.

    """
    if (await app['pool'].fetchval(_Q_DELETE_DOC, docid, etags)) is None:
        # the operation may fail because either the id doesn't exist or the given
        # etag doesn't match. There's no way to atomically check for both
        # conditions at the same time, apart from a full table lock. However,
        # all scenario's in which the below, not threat-safe way of identifying
        # the cause of failure is not correct, are trivial.
        _, etag = await storage_retrieve(docid, etags)  # this may raise a KeyError
        assert etag not in etags
        raise ValueError


def _extract_values(elm, ptr_parts, ptr_idx=0):
    """Recursive generator that yields all values that may live under the
    given JSON pointer."""
    if ptr_idx == len(ptr_parts):
        yield elm
        return
    part = ptr_parts[ptr_idx]
    if part == 'properties':
        if ptr_idx == len(ptr_parts) - 1:
            raise ValueError('Properties must be followed by property name')
        key = ptr_parts[ptr_idx+1]
        if type(elm) is not dict:
            _logger.debug('Expected obj with key {}, got {}'.format(key, type(elm)))
        elif key in elm:
            for e in _extract_values(elm[key], ptr_parts, ptr_idx + 2):
                yield e
        else:
            _logger.debug('Obj does not have key {}'.format(key))
    elif part == 'items':
        if type(elm) is not list:
            _logger.debug('Expected array, got {}'.format(repr(elm)))
        else:
            for item in elm:
                for e in _extract_values(item, ptr_parts, ptr_idx + 1):
                    yield e
    else:
        raise ValueError('Element must be either list, object or end of pointer, not: ' + part)


@_hookimpl
async def storage_extract(app: T.Mapping, ptr: str, distinct: bool=False) -> T.Generator[str, None, None]:
    # language=rst
    """Generator to extract values from the stored documents, optionally
    distinct.

    Used to, for example, get a list of all tags or ids in the system. Or to
    get all documents stored in the system. If distinct=True then the generator
    will cache all values in a set, which may become prohibitively large.

    :param ptr: JSON pointer to the element.
    :param distinct: Return only distinct values.
    :raises: ValueError if filter syntax is invalid.
    """
    # If the pointer is '/' we should return all documents
    if ptr == '/':
        async with app['pool'].acquire() as con:
            async with con.transaction():
                # use a cursor so we can stream
                async for row in con.cursor(_Q_RETRIEVE_ALL_DOCS):
                    yield json.loads(row['doc'])
        return

    # Otherwise, return the values
    try:
        p = jsonpointer.JsonPointer(ptr)
    except jsonpointer.JsonPointerException:
        raise ValueError('Cannot parse pointer')
    ptr_parts = p.parts

    cache = set()
    async with app['pool'].acquire() as con:
        async with con.transaction():
            # use a cursor so we can stream
            async for row in con.cursor(_Q_RETRIEVE_ALL_DOCS):
                doc = json.loads(row['doc'])
                for elm in _extract_values(doc, ptr_parts):
                    if not distinct or elm not in cache:
                        yield elm
                        if distinct:
                            cache.add(elm)


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
async def search_search(
    app, q: str, sortpath: T.List[str],
    result_info: T.MutableMapping,
    facets: T.Optional[T.Iterable[str]]=None,
    limit: T.Optional[int]=None, offset: int=0,
    filters: T.Optional[T.Mapping[
        str,  # a JSON pointer
        T.Mapping[
            str,  # a comparator; one of ``eq``, ``in``, ``lt``, ``gt``, ``le`` or ``ge``
            # a string, or a set of strings if the comparator is ``in``
            T.Union[str, T.Set[str]]
        ]
    ]]=None,
    iso_639_1_code: T.Optional[str]=None
) -> T.AsyncGenerator[T.Tuple[str, dict], None]:
    # language=rst
    """ Search

    See :func:`datacatalog.plugin_interfaces.search_search`

    """
    # parse facets, if any
    if facets is None:
        facets = []
    else:
        try:
            facets = [(f, jsonpointer.JsonPointer(f)) for f in facets]
        except jsonpointer.JsonPointerException:
            raise ValueError('Cannot parse pointer')
    # interpret the filters
    filterexpr = _to_pg_json_filterexpression(filters)
    # interpret the language
    lang = _to_pg_lang(iso_639_1_code)
    # init paging parameters
    start, end = offset, offset+limit if limit is not None else float('inf')
    # keep track of the current row index
    row_index = 0
    # if we have a query we should perform a free-text search ordered by
    # relevance, otherwise we should do a sorted listing.
    if len(q) > 0:
        result_iterator = _execute_search_query(app, filterexpr, lang, q)
    else:
        result_iterator = _execute_list_query(app, filterexpr, lang, sortpath)
    # now iterate over the results
    async for docid, doc in result_iterator:
        # update the result info
        for facet, ptr in facets:
            if facet not in result_info:
                result_info[facet] = {}
            ptr_parts = ptr.parts
            for value in _extract_values(doc, ptr_parts):
                value = str(value)
                if value not in result_info[facet]:
                    result_info[facet][value] = 1
                else:
                    result_info[facet][value] += 1
        # yield the result if it falls within the current page
        if start <= row_index < end:
            yield (docid, doc)

        row_index += 1
    # store the total amount of documents in the result info
    result_info['/'] = row_index


async def _execute_list_query(app, filterexpr: str, lang: str, sortpath: T.List[str]):
    if len(sortpath) == 0:
        raise ValueError('Sortpath should not be empty')
    sortexpr = 'doc->'
    for p in sortpath[:-1]:
        sortexpr += "'" + p + "'->"
    sortexpr += ">'" + sortpath[-1] + "'"
    async with app['pool'].acquire() as con:
        # use a cursor so we can stream
        async with con.transaction():
            stmt = await con.prepare(
                _Q_LIST_DOCS.format(filters=filterexpr, sortexpression=sortexpr)
            )
            async for row in stmt.cursor(lang):
                yield row['id'], json.loads(row['doc'])


async def _execute_search_query(app, filterexpr: str, lang: str, q: str):
    query = _to_pg_json_query(q)
    async with app['pool'].acquire() as con:
        # use a cursor so we can stream
        async with con.transaction():
            stmt = await con.prepare(
                _Q_SEARCH_DOCS.format(filters=filterexpr)
            )
            async for row in stmt.cursor(lang, query):
                yield row['id'], json.loads(row['doc'])


def _to_pg_json_filterexpression(filters: T.Optional[dict]) -> str:
    if filters is None:
        return ''

    def to_expr(ptr: str, value: T.Any) -> str:
        """Create a filterexpression from a json pointer and value."""
        try:
            p = jsonpointer.JsonPointer(ptr)
        except jsonpointer.JsonPointerException:
            raise ValueError('Cannot parse pointer')
        parts = collections.deque(p.parts)
        value = json.dumps(value)

        def parse_complex_type():
            nxt = parts.popleft()
            if nxt == 'properties':
                return parse_obj()
            elif nxt == 'items':
                return parse_list()
            raise ValueError('Child must be either list, '
                             'object or end of pointer, not: ' + nxt)

        def parse_obj() -> str:
            if len(parts) == 0:
                raise ValueError('Properties must be followed by property name')
            name = json.dumps(parts.popleft())
            # either end-of-pointer primitive...
            if len(parts) == 0:
                return '{' + name + ': ' + value + '}'
            # or a complex type
            return '{' + name + ': ' + parse_complex_type() + '}'

        def parse_list() -> str:
            # either end-of-pointer primitive...
            if len(parts) == 0:
                return '[' + value + ']'
            # or a complex type
            return '[' + parse_complex_type() + ']'

        # base case: query json document with solely a single primitive
        # (string, int, bool, ...)
        if len(parts) == 0:
            return value

        # anything else must be a complex type (object or list)
        return parse_complex_type()

    # Interpret the filters
    filterexprs = []
    for ptr, filter in filters.items():
        for op, val in filter.items():
            if op != 'eq' and op != 'in':
                raise NotImplementedError(
                    'Postgres plugin only supports '
                    '"eq" and "in" filter operators')
            if op == "eq":
                filterexprs.append(
                    " AND doc @> '" + to_expr(ptr, val) + "'")
            elif op == "in":
                orexpr = ' OR '.join(
                    "doc @> '" + to_expr(ptr, v) + "'" for v in val
                )
                filterexprs.append(' AND (' + orexpr + ')')
    return ''.join(filterexprs)


def _to_pg_lang(iso_639_1_code: str) -> str:
    if iso_639_1_code is None:
        return 'simple'
    if iso_639_1_code not in ISO_639_1_TO_PG_DICTIONARIES:
        raise ValueError(
            'invalid ISO 639-1 language code: ' + iso_639_1_code)
    return ISO_639_1_TO_PG_DICTIONARIES[iso_639_1_code]


def _to_pg_json_query(q: str) -> str:
    return ' | '.join("{}:*".format(t) for t in q.split())


def _etag_from_str(s: str) -> str:
    h = hashlib.sha3_224()
    h.update(s.encode())
    return '"' + base64.urlsafe_b64encode(h.digest()).decode() + '"'


def _iso_639_1_code_to_pg(iso_639_1_code: str) -> str:
    # we use the simple dictionary for ISO 639-1 language codes we don't know
    if iso_639_1_code not in ISO_639_1_TO_PG_DICTIONARIES:
        if iso_639_1_code is not None:
            _logger.warning('invalid ISO 639-1 language code: ' + iso_639_1_code)
        return 'simple'
    return ISO_639_1_TO_PG_DICTIONARIES[iso_639_1_code]
