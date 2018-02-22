import typing as T

from aiopluggy import HookspecMarker


hookspec = HookspecMarker('datacatalog')


#################
# Generic Hooks #
#################

# noinspection PyUnusedLocal
@hookspec.replay.sync
def initialize_sync(app) -> None:
    # language=rst
    """The first method to be called by the plugin-manager.

    If your plugin needs to do some *asynchronous* initialization, try
    :func:`initialize`

    :param app: the :class:`~datacatalog.app.Application` object.

    """


# noinspection PyUnusedLocal
@hookspec.replay
def initialize(app) -> None:
    # language=rst
    """Called by the plugin-manager when the event loop starts.

    If your plugin needs to do some initialization even before the event loop
    starts, you'll need to do this in :func:`initialize_sync`.

    :param app: the :class:`~datacatalog.app.Application` object.

    """


# noinspection PyUnusedLocal
@hookspec
def deinitialize(app) -> None:
    # language=rst
    """Called when the application shuts down.

    :param app: the :class:`~datacatalog.app.Application` object.

    """


# noinspection PyUnusedLocal
@hookspec
def health_check() -> T.Optional[str]:
    # language=rst
    """Health check.

    :returns: If unhealthy, a string describing the problem, otherwise ``None``.
    :raises Exception: if that's easier than returning a string.

    """


#################
# Storage Hooks #
#################

# noinspection PyUnusedLocal
@hookspec.first_only.required
def storage_retrieve(id: str) -> T.Tuple[dict, str]:
    # language=rst
    """ Get document and corresponsing etag by id.

    :returns: a "JSON dictionary"
    :raises KeyError: if not found

    """


# noinspection PyUnusedLocal
@hookspec.first_only.required
def storage_get_from_doc(ptr: str, distinct: bool=False) -> T.Generator[str, None, None]:
    # language=rst
    """Generator to extract values from the stored documents, optionally
    distinct.

    Used to, for example, get a list of all tags or ids in the system. Or to
    get all documents stored in the system.

    :param ptr: JSON pointer to the element.
    :param distinct: Return only distinct values.
    :raises: ValueError if filter syntax is invalid.
    """


# noinspection PyUnusedLocal
@hookspec.first_only
def storage_store(
        id: str, doc: dict, searchable_text: str,
        iso_639_1_code: T.Optional[str], etag: T.Optional[str]) -> str:
    # language=rst
    """ Store document.

    :param id: the ID under which to store this document. May or may not
        already exist in the data store.
    :param doc: the document to store; a "JSON dictionary".
    :param searchable_text: this will be indexed for free-text search.
    :param iso_639_1_code: the language of the document. Will be used for
        free-text search indexing.
    :param etag: the last known ETag of this document, or ``None`` if no
        document with this ``id`` should exist yet.
    :returns: new ETag
    :raises: ValueError if the given etag doesn't match the stored etag, or if
             no etag is given while the doc identifier already exists.
    :raises: KeyError if the call is an update (i.e. an etag is given) but the
             identifier doesn't exist.

    """


# noinspection PyUnusedLocal
@hookspec.first_only
def storage_delete(id: str, etag: str) -> None:
    # language=rst
    """ Delete document.

    :param id: the ID of the document to delete.
    :param etag: the last known ETag of this document.
    :raises: ValueError if the given etag doesn't match the stored etag.
    :raises: KeyError if a document with the given id doesn't exist.

    """


# noinspection PyUnusedLocal
@hookspec.first_only
def storage_id() -> str:
    # language=rst
    """New unique identifier."""


################
# Search Hooks #
################

# noinspection PyUnusedLocal
@hookspec
def search_search(
    q: str, limit: T.Optional[int],
    cursor: T.Optional[str],
    filters: T.Optional[T.Mapping[
        str, # a JSON pointer
        T.Mapping[
            str, # a comparator; one of ``eq``, ``in``, ``lt``, ``gt``, ``le`` or ``ge``
            # a string, or a set of strings if the comparator is ``~``
            T.Union[str, T.Set[str]]
        ]
    ]],
    iso_639_1_code: T.Optional[str]
) -> T.Tuple[T.Generator[T.Tuple[dict, str], None, None], str]:
    # language=rst
    """ Search.

    :param q: the query
    :param limit: maximum hits to be returned
    :param cursor: TODO: documentation
    :param filters: mapping of JSON pointer -> value, used to filter on some value.
    :param iso_639_1_code: the language of the query.
    :returns: A tuple with a generator over the search results (documents with corresponding etags), and the cursor.
    :raises: ValueError if filter syntax is invalid, or if the ISO 639-1 code is not recognized.

    """


####################
# Metadata Schemas #
####################

# noinspection PyUnusedLocal
# @hookspec
# def mds_convert(from_schema: str, to_schema: str, data: dict) -> T.Optional[dict]:
#     # language=rst
#     """Convert metadata from one schema to another.
#
#     :param from_schema: the schema of ``data``
#     :param to_schema: the schema to convert ``data`` to
#     :param data: the data to convert
#
#     """


# noinspection PyUnusedLocal
@hookspec.first_only.sync
def mds_name() -> str:
    # language=rst
    """The schema this plugin provides.

    :returns: a string that is safe for use in a URL segment; ie. every string
        that matches regular expression
        ``^(?:%[a-f0-9]{2}|[-\w:@!$&'()*+,;=.~])*$``

    """


@hookspec.first_only
def mds_normalize(data: dict) -> dict:
    # language=rst
    """Normalize the given document according to this schema.

    :returns: dict with normalized entries

    """


# noinspection PyUnusedLocal
@hookspec.first_only
def mds_json_schema() -> dict:
    # language=rst
    """The json schema.
    """


# noinspection PyUnusedLocal
@hookspec.first_only
def mds_full_text_search_representation(data: dict) -> str:
    # language=rst
    """Full text search representation of the given data.
    """
