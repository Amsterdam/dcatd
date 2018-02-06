import typing as T
import abc

from aiopluggy import HookspecMarker


hookspec = HookspecMarker('datacatalog')


#################
# Generic Hooks #
#################


# noinspection PyUnusedLocal
@hookspec.replay.sync
def initialize_sync(app) -> T.Optional[T.Coroutine]:
    # language=rst
    """ The first method to be called by the plugin-manager.

    If your plugin needs to do some *asynchronous* initialization, try
    :func:`initialize`

    """


# noinspection PyUnusedLocal
@hookspec.replay
def initialize(app) -> T.Optional[T.Coroutine]:
    # language=rst
    """ Called by the plugin-manager when the event loop starts.

    If your plugin needs to do some initialization even before the event loop
    starts, you'll need to do this in :func:`initialize_sync`.

    """


# noinspection PyUnusedLocal
@hookspec
def deinitialize(app) -> None:
    # language=rst
    """ Called when the application shuts down."""


# noinspection PyUnusedLocal
@hookspec
def health_check() -> T.Optional[str]:
    # language=rst
    """ Health check.

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
def search_search(q: str, limit: T.Optional[int],
                  offset: T.Optional[int],
                  filters: T.Optional[T.Mapping[str, str]],
                  iso_639_1_code: T.Optional[str]
                  ) -> T.Tuple[T.Generator[T.Tuple[dict, str], None, None], str]:
    # language=rst
    """ Search.

    :param q: the query.
    :param limit: maximum hits to be returned.
    :param offset: starting offset.
    :param filters: mapping of JSON pointer -> value, used to filter on some value.
    :param iso_639_1_code: the language of the query.
    :returns: A tuple with a generator over the search results (documents with corresponding etags), and the cursor.
    :raises: ValueError if filter syntax is invalid, or if the ISO 639-1 code is not recognized.

    """


#######################
# Metadata Convertors #
#######################

# noinspection PyUnusedLocal
@hookspec
def mdc_convert(from_profile, to_profile, data):
    # language=rst
    """ Convert metadata from one profile to another.
    """


####################
# Metadata Profile #
####################

# noinspection PyUnusedLocal
@hookspec
def mdp_something():
    # language=rst
    """

    .. todo:: define

    """
