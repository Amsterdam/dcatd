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

_pool: asyncpg.pool.Pool = None
_hookimpl = aiopluggy.HookimplMarker('datacatalog')
_logger = logging.getLogger('plugin.storage.postgres')

CONNECT_ATTEMPT_INTERVAL_SECS = 2
CONNECT_ATTEMPT_MAX_TRIES = 5

_Q_CREATE = """
CREATE TABLE IF NOT EXISTS "dataset" (
    id character varying(50) PRIMARY KEY,
    doc jsonb NOT NULL,
    etag character varying(254) NOT NULL,
    searchable_text tsvector,
    lang character varying(20)
);
CREATE INDEX IF NOT EXISTS idx_id_etag ON "dataset" (id, etag);
CREATE INDEX IF NOT EXISTS idx_full_text_search ON "dataset" USING gin (searchable_text);
CREATE INDEX IF NOT EXISTS idx_json_docs ON "dataset" USING gin (doc jsonb_path_ops);
"""
_Q_HEALTHCHECK = 'SELECT 1'
_Q_RETRIEVE_DOC = 'SELECT doc, etag FROM "dataset" WHERE id = $1'
_Q_INSERT_DOC = 'INSERT INTO "dataset" (id, doc, searchable_text, lang, etag) VALUES ($1, $2, to_tsvector($3, $4), $3, $5)'
_Q_UPDATE_DOC = 'UPDATE "dataset" SET doc=$1, searchable_text=to_tsvector($2, $3), lang=$2, etag=$4 WHERE id=$5 AND etag=ANY($6) RETURNING id'
_Q_DELETE_DOC = 'DELETE FROM "dataset" WHERE id=$1 AND etag=ANY($2) RETURNING id'
_Q_RETRIEVE_ALL_DOCS = 'SELECT doc FROM "dataset"'
_Q_SEARCH_DOCS = """
SELECT doc, etag, ts_rank_cd(searchable_text, query) AS rank 
FROM "dataset", plainto_tsquery($1, $2) query
WHERE (''=$2::varchar OR searchable_text @@ query) {}
AND ('simple'=$1::varchar OR lang=$1::varchar)
ORDER BY rank DESC
LIMIT $3
OFFSET $4;
"""
# TODO: This search query uses one a default ranking algorihm.


@_hookimpl
async def initialize(app) -> T.Optional[T.Coroutine]:
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
    with pkg_resources.resource_stream(__name__, 'postgres_config_schema.yml') as s:
        schema = yaml.load(s)
    app.config.validate(schema)

    # create asyncpg engine
    dbconf = app.config['storage_postgres']
    _logger.info("Connecting to database: postgres://%s:%i/%s",
                 dbconf['host'], dbconf['port'], dbconf['name'])

    connect_attempt_tries_left = CONNECT_ATTEMPT_MAX_TRIES - 1
    while connect_attempt_tries_left >= 0:
        try:
            _pool = await asyncpg.create_pool(
                user=dbconf['user'],
                database=dbconf['name'],
                host=dbconf['host'],
                port=dbconf['port'],
                password=dbconf['pass'],
                loop=app.loop
            )
        except ConnectionRefusedError:
            if connect_attempt_tries_left > 0:
                connect_attempt_tries_left -= 1
                _logger.warning("Database not accepting connections. Retrying %d more times.", connect_attempt_tries_left)
                await asyncio.sleep(CONNECT_ATTEMPT_INTERVAL_SECS)
            else:
                _logger.error("Could not connect to the database. Aborting.")
                raise
        else:
            break
    await _pool.execute(_Q_CREATE)


@_hookimpl
async def health_check() -> T.Optional[str]:
    # language=rst
    """ Health check.

    :returns: If unhealthy, a string describing the problem, otherwise ``None``.
    :raises Exception: if that's easier than returning a string.

    """
    if (await _pool.fetchval(_Q_HEALTHCHECK)) != 1:
        return 'Postgres connection problem'


@_hookimpl
async def storage_retrieve(docid: str, etags: T.Optional[T.Set[str]]) \
        -> T.Optional[T.Tuple[dict, str]]:
    # language=rst
    """ Get document and corresponsing etag by id.

    :param docid: document id
    :param etags: None, or a set of Etags
    :returns:
        Either a tuple containing the document and current etag, or None if the
        document's Etag corresponds to one of the given etags.
    :raises KeyError: if not found

    """
    record = await _pool.fetchrow(_Q_RETRIEVE_DOC, docid)
    if record is None:
        raise KeyError()
    if etags and conditional.match_etags(record['etag'], etags, True):
        return None
    return json.loads(record['doc']), record['etag']


@_hookimpl
async def storage_create(docid: str, doc: dict, searchable_text: str,
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
        await _pool.execute(_Q_INSERT_DOC, docid, new_doc, lang, searchable_text, new_etag)
    except asyncpg.exceptions.UniqueViolationError as e:
        raise KeyError from e
    return new_etag


@_hookimpl
async def storage_update(docid: str, doc: dict, searchable_text: str,
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
    if (await _pool.fetchval(_Q_UPDATE_DOC, new_doc, lang, searchable_text, new_etag, docid, list(etags))) is None:
        raise ValueError
    return new_etag


@_hookimpl
async def storage_delete(docid: str, etags: T.Set[str]) -> None:
    # language=rst
    """ Delete document only if it has one of the provided Etags.

    :param docid: the ID of the document to delete.
    :param etags: the last known ETags of this document.
    :raises: ValueError if none of the given etags match the stored etag.
    :raises: KeyError if a document with the given id doesn't exist.

    """
    if (await _pool.fetchval(_Q_DELETE_DOC, docid, etags)) is None:
        # the operation may fail because either the id doesn't exist or the given
        # etag doesn't match. There's no way to atomically check for both
        # conditions at the same time, apart from a full table lock. However,
        # all scenario's in which the below, not threat-safe way of identifying
        # the cause of failure is not correct, are trivial.
        doc = await storage_retrieve(docid, etags)  # this may raise a KeyError
        assert doc is not None
        raise ValueError


@_hookimpl
async def storage_extract(ptr: str, distinct: bool=False) -> T.Generator[str, None, None]:
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
        async with _pool.acquire() as con:
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
    num_parts = len(ptr_parts)

    def values(ptr_idx, elm):
        """Recursive generator that yields all values that may live under the
        given JSON pointer."""
        if ptr_idx == num_parts:
            yield elm
            return
        part = ptr_parts[ptr_idx]
        if part == 'properties':
            if ptr_idx == num_parts-1:
                raise ValueError('Properties must be followed by property name')
            key = ptr_parts[ptr_idx+1]
            if type(elm) is not dict:
                _logger.debug('Expected obj with key {}, got {}'.format(key, type(elm)))
            elif key in elm:
                for e in values(ptr_idx+2, elm[key]):
                    yield e
            else:
                _logger.debug('Obj does not have key {}'.format(key))
        elif part == 'items':
            if type(elm) is not list:
                _logger.debug('Expected array, got {}'.format(type(elm)))
            else:
                for item in elm:
                    for e in values(ptr_idx+1, item):
                        yield e
        else:
            raise ValueError('Element must be either list, object or end of pointer, not: ' + part)

    cache = set()
    async with _pool.acquire() as con:
        async with con.transaction():
            # use a cursor so we can stream
            async for row in con.cursor(_Q_RETRIEVE_ALL_DOCS):
                doc = json.loads(row['doc'])
                for elm in values(0, doc):
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
        q: str, limit: T.Optional[int],
        cursor: T.Optional[str],
        filters: T.Optional[T.Mapping[
            str, # a JSON pointer
            T.Mapping[
                str, # a comparator; one of ``eq``, ``in``, ``lt``, ``gt``, ``le`` or ``ge``
                # a string, or a set of strings if the comparator is ``in``
                T.Union[str, T.Set[str]]
            ]
        ]],
        iso_639_1_code: T.Optional[str]
) -> T.Generator[T.Tuple[dict, str], None, None]:
    # language=rst
    """ Search.

    :param q: the query
    :param limit: maximum hits to be returned
    :param cursor: TODO: documentation
    :param filters: mapping of JSON pointer -> value, used to filter on some value.
    :param iso_639_1_code: the language of the query.
    :returns: A tuple with a generator over the search results (documents with corresponding etags)
    :raises: ValueError if filter syntax is invalid, or if the ISO 639-1 code is not recognized.

    """

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
            raise ValueError('Child must be either list, object or end of pointer, not: ' + nxt)

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

    # Interpret the language
    lang = 'simple'
    if iso_639_1_code is not None:
        if iso_639_1_code not in _iso_639_1_to_pg_dictionaries:
            raise ValueError('invalid ISO 639-1 language code: ' + iso_639_1_code)
        else:
            lang = _iso_639_1_to_pg_dictionaries[iso_639_1_code]

    # Interpret the filters (to_expr calls json.dumps on both the json pointers
    # and corresponding values, so we don't escape separately and use a format
    # string).
    filterexprs = []
    if filters:
        for ptr, filter in filters.items():
            for op, val in filter.items():
                if op != 'eq' and op != 'in':
                    raise NotImplementedError('Postgres plugin only supports "eq" and "in" filter operators')
                if op == "eq":
                    filterexprs.append(" AND doc @> '" + to_expr(ptr, val) + "'")
                elif op == "in":
                    orexpr = ' OR '.join("doc @> '" + to_expr(ptr, v) + "'" for v in val)
                    filterexprs.append(' AND (' + orexpr + ')')
    filterexpr = ''.join(filterexprs)

    # Interpret paging
    if cursor is None:
        offset = 0
    else:
        base64.decodebytes(cursor.encode())
    if limit is None:
        limit = 'ALL'

    async with _pool.acquire() as con:
        async with con.transaction():
            # use a cursor so we can stream
            sql = _Q_SEARCH_DOCS.format(filterexpr)
            async for row in con.cursor(sql, lang, q, limit, offset):
                yield row['doc'], row['etag']


def _etag_from_str(s: str) -> str:
    h = hashlib.sha3_224()
    h.update(s.encode())
    return '"' + base64.urlsafe_b64encode(h.digest()).decode() + '"'


def _iso_639_1_code_to_pg(iso_639_1_code: str) -> str:
    # we use the simple dictionary for ISO 639-1 language codes we don't know
    if iso_639_1_code not in _iso_639_1_to_pg_dictionaries:
        if iso_639_1_code is not None:
            _logger.warning('invalid ISO 639-1 language code: ' + iso_639_1_code)
        return 'simple'
    return _iso_639_1_to_pg_dictionaries[iso_639_1_code]


# The below maps ISO 639-1 language codes (as used in dcat) to pg dictionaries.
# Note that a default postgres installation comes with a limited set of
# dictionaries; on my system, danish, dutch, english, finnish, french,
# german, hungarian, italian, norwegian, portuguese, romanian, russian, simple,
# spanish, swedish and turkish. If you need support for a different language
# you will need to install that dictionary and register it under the name
# listed in the below mapping. You may also want to experiment with Ispell or
# Snowball dictionaries. See more info at
# https://www.postgresql.org/docs/current/static/textsearch-dictionaries.html
_iso_639_1_to_pg_dictionaries = {
    'aa': 'afar',
    'ab': 'abkhazian',
    'af': 'afrikaans',
    'am': 'amharic',
    'ar': 'arabic',
    'as': 'assamese',
    'ay': 'aymara',
    'az': 'azerbaijani',
    'ba': 'bashkir',
    'be': 'byelorussian',
    'bg': 'bulgarian',
    'bh': 'bihari',
    'bi': 'bislama',
    'bn': 'bengali',
    'bo': 'tibetan',
    'br': 'breton',
    'ca': 'catalan',
    'co': 'corsican',
    'cs': 'czech',
    'cy': 'welch',
    'da': 'danish',
    'de': 'german',
    'dz': 'bhutani',
    'el': 'greek',
    'en': 'english',
    'eo': 'esperanto',
    'es': 'spanish',
    'et': 'estonian',
    'eu': 'basque',
    'fa': 'persian',
    'fi': 'finnish',
    'fj': 'fiji',
    'fo': 'faeroese',
    'fr': 'french',
    'fy': 'frisian',
    'ga': 'irish',
    'gd': 'scots gaelic',
    'gl': 'galician',
    'gn': 'guarani',
    'gu': 'gujarati',
    'ha': 'hausa',
    'he': 'hebrew',
    'hi': 'hindi',
    'hr': 'croatian',
    'hu': 'hungarian',
    'hy': 'armenian',
    'ia': 'interlingua',
    'id': 'indonesian',
    'ie': 'interlingue',
    'ik': 'inupiak',
    'in': 'indonesian',
    'is': 'icelandic',
    'it': 'italian',
    'iu': 'inuktitut',
    'iw': 'hebrew',
    'ja': 'japanese',
    'ji': 'yiddish',
    'jw': 'javanese',
    'ka': 'georgian',
    'kk': 'kazakh',
    'kl': 'greenlandic',
    'km': 'cambodian',
    'kn': 'kannada',
    'ko': 'korean',
    'ks': 'kashmiri',
    'ku': 'kurdish',
    'ky': 'kirghiz',
    'la': 'latin',
    'ln': 'lingala',
    'lo': 'laothian',
    'lt': 'lithuanian',
    'lv': 'latvian',
    'mg': 'malagasy',
    'mi': 'maori',
    'mk': 'macedonian',
    'ml': 'malayalam',
    'mn': 'mongolian',
    'mo': 'moldavian',
    'mr': 'marathi',
    'ms': 'malay',
    'mt': 'maltese',
    'my': 'burmese',
    'na': 'nauru',
    'ne': 'nepali',
    'nl': 'dutch',
    'no': 'norwegian',
    'oc': 'occitan',
    'om': 'oromo',
    'or': 'oriya',
    'pa': 'punjabi',
    'pl': 'polish',
    'ps': 'pashto',
    'pt': 'portuguese',
    'qu': 'quechua',
    'rm': 'rhaeto-romance',
    'rn': 'kirundi',
    'ro': 'romanian',
    'ru': 'russian',
    'rw': 'kinyarwanda',
    'sa': 'sanskrit',
    'sd': 'sindhi',
    'sg': 'sangro',
    'sh': 'serbo-croatian',
    'si': 'singhalese',
    'sk': 'slovak',
    'sl': 'slovenian',
    'sm': 'samoan',
    'sn': 'shona',
    'so': 'somali',
    'sq': 'albanian',
    'sr': 'serbian',
    'ss': 'siswati',
    'st': 'sesotho',
    'su': 'sudanese',
    'sv': 'swedish',
    'sw': 'swahili',
    'ta': 'tamil',
    'te': 'tegulu',
    'tg': 'tajik',
    'th': 'thai',
    'ti': 'tigrinya',
    'tk': 'turkmen',
    'tl': 'tagalog',
    'tn': 'setswana',
    'to': 'tonga',
    'tr': 'turkish',
    'ts': 'tsonga',
    'tt': 'tatar',
    'tw': 'twi',
    'ug': 'uigur',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'vo': 'volapuk',
    'wo': 'wolof',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'za': 'zhuang',
    'zh': 'chinese',
    'zu': 'zulu'
}