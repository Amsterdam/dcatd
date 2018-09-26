import typing as T

from aiopluggy import HookspecMarker

from datacatalog.dcat import Direction

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
def health_check(app) -> T.Optional[str]:
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
def storage_retrieve(app, docid: str, etags: T.Optional[T.Set[str]]) \
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


# noinspection PyUnusedLocal
@hookspec.first_only.required
def storage_create(app, docid: str, doc: dict, searchable_text: str,
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


# noinspection PyUnusedLocal
@hookspec.first_only.required
def storage_update(app, docid: str, doc: dict, searchable_text: str,
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


# noinspection PyUnusedLocal
@hookspec.first_only.required
def storage_delete(app, docid: str, etags: T.Set[str]) -> None:
    # language=rst
    """ Delete document only if it has one of the provided Etags.

    :param docid: the ID of the document to delete.
    :param etags: the last known ETags of this document.
    :raises: ValueError if none of the given etags match the stored etag.
    :raises: KeyError if a document with the given id doesn't exist.

    """


# noinspection PyUnusedLocal
@hookspec.first_only.required
def storage_extract(app, ptr: str, distinct: bool=False) -> T.Generator[str, None, None]:
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
@hookspec.first_only.required
def storage_id() -> str:
    # language=rst
    """New unique identifier."""


################
# Object Store #
################

# noinspection PyUnusedLocal
# @hookspec.first_only
# def _put_file_to_object_store(name,
#                         content_type,
#                         stream) -> T.AsyncContextManager:
#     # language=rst
#     """Asynchronous context manager for file storage.
#
#     The *context* must implement an asynchronous ``write(data: bytes)`` method.
#
#     :param str name: file name under which to store the data
#     :param str content_type: the content type of the file
#     :param aiohttp.StreamReader stream: the data to store
#
#     """


################
# Search Hooks #
################

# noinspection PyUnusedLocal
@hookspec.first_only.required
def search_search(
    app, q: str, sortpath: T.List[str],
    result_info: T.MutableMapping,
    facets: T.Optional[T.Iterable[str]]=None,
    limit: T.Optional[int]=None, offset: T.Optional[int]=0,
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
    """ Search.

    :param app: global dictionary
    :param q: the query
    :param sortproperty: the property to sort by. Must be a top-level object property.
    :param result_info: mapping in which all encountered facets in the result set are
        put
    :param facets: a list of facets to return and count
    :param limit: maximum hits to be returned
    :param offset: offset in resultset
    :param filters: mapping of JSON pointer -> value, used to filter on some
        value.
    :param iso_639_1_code: the language of the query
    :returns: A generator over the search results (id, doc, metadata)
    :raises: ValueError if filter syntax is invalid, if the ISO 639-1 code is
        not recognized, or if the offset is invalid.

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
def mds_canonicalize(data: dict, id: T.Optional[str]=None, direction: Direction=Direction.GET) -> dict:
    # language=rst
    """Canonicalize the given document according to this schema.

    :returns: dict with canonicalized entries

    """


# noinspection PyUnusedLocal
@hookspec.first_only
def mds_json_schema(app) -> dict:
    # language=rst
    """The json schema.
    """


# noinspection PyUnusedLocal
@hookspec.first_only
def mds_full_text_search_representation(data: dict) -> str:
    # language=rst
    """Full text search representation of the given data.
    """


# noinspection PyUnusedLocal
@hookspec.first_only
def mds_context() -> dict:
    # language=rst
    """Context of the metadata schema.
    """

# noinspection PyUnusedLocal
@hookspec.first_only
def check_startup_action(app, name: str) -> bool:
    # language=rst
    """Check if action has been done
    """

# noinspection PyUnusedLocal
@hookspec.first_only
async def add_startup_action(app, name: str):
    # language=rst
    """Set action to done
    """


# noinspection PyUnusedLocal
@hookspec.first_only
async def get_old_identifiers(app):
    # language=rst
    """Get old identifiers
    """


# noinspection PyUnusedLocal
@hookspec.first_only
async def set_new_identifier(app, old_id: str, new_id: str):
    # language=rst
    """Set new identifier
    """

# noinspection PyUnusedLocal
@hookspec.first_only
async def storage_all(app: T.Mapping) -> T.AsyncGenerator[T.Tuple[str, str, dict], None]:
    # language=rst
    """Get all data
    """