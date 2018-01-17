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
    """ Called by the plugin-manager when event loop starts.

    If your plugin needs to do some initialization even before the event loop
    starts, you'll need to do this in :func:`initialize_sync`.

    """


# noinspection PyUnusedLocal
@hookspec
def deinitialize(app):
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
@hookspec.first_result.required
def storage_retrieve(id: str) -> dict:
    # language=rst
    """ Get document by id.

    :returns: a "JSON dictionary"
    :raises KeyError: if not found

    """


# noinspection PyUnusedLocal
@hookspec.required
def storage_retrieve_list():
    # language=rst
    """ Unknown signature.
    """


# noinspection PyUnusedLocal
@hookspec.first_result
def storage_store(id: str, doc: dict, etag: T.Optional[str]) -> str:
    # language=rst
    """ Store document.

    :param id: the ID under which to store this document. May or may not
        already exist in the data store.
    :param doc: the document to store; a "JSON dictionary".
    :param etag: the last known ETag of this document, or ``None`` if no
        document with this ``id`` should exist yet.
    :returns: new ETag

    """


# noinspection PyUnusedLocal
@hookspec.first_result
def storage_id() -> str:
    # language=rst
    """New unique identifier."""


################
# Search Hooks #
################

# noinspection PyUnusedLocal
@hookspec
def search_search(query: T.Optional[T.Mapping]=None):
    # language=rst
    """ Search.

    .. todo:: documentation, return value type

    """


class AbstractPlugin(abc.ABC):
    """Parent of all plugin interface classes."""

    @classmethod
    def implemented_by(cls: abc.ABC, plugin) -> bool:
        # language=rst
        """

        Returns:
            ``True`` if ``plugin`` implements all abstact methods in ``cls``.
            Otherwise, the normal algorithm for subclass detection is invoked,
            which will probably return ``False``.

        """
        return all(
            hasattr(plugin, abstract_method_name) and
            callable(getattr(plugin, abstract_method_name))
            for abstract_method_name in cls.__abstractmethods__
        )

    def __init__(self, app):
        # language=rst
        """Default constructor.

        Arguments:
            app (datacatalog.application.Application): the application

        Does nothing.

        """

    async def plugin_start(self, app):
        # language=rst
        """Called before application start.

        If your plugin needs to perform some asynchronous initialization, you can do it in this method.

        Raises:
            Exception: if initialization failed.

        """

    async def plugin_stop(self, app):
        # language=rst
        """Called before application start.

        If your plugin needs to perform some asynchronous initialization, you can do it in this method.

        Raises:
            Exception: if teardown failed.

        """


class AbstractFullTextSearchPlugin(AbstractPlugin):
    # language=rst
    """Fuzzy full text search engine interface.

    .. warning:: Unused. Work in progress.

    """

    @abc.abstractmethod
    async def fts_index(self, identifier: str, texts: T.Iterable[str]):
        # language=rst
        """Build a full-text search index for a document.

        Args:
            identifier: the identifier of the document from which the texts have
                been extracted.
            texts: the texts extracted from the document.

        """
        pass

    @abc.abstractmethod
    async def fts_search(self, query: str, max_length: int) -> T.List[T.Tuple[str, T.Iterable[str]]]:
        # language=rst
        """Retrieve documents satisfying some text query.

        Args:
            query: a full text query string. Format may be plugin-specific.


        Returns:
            a list of tuples, ordered by relevance, with each tuple containing:

            -   the document identifier
            -   a list of pieces of text matching the query. If the search
                engine doesn't support such a preview feature, the list may be
                empty.

        """

    @abc.abstractmethod
    async def fts_search_filtered(self,
                                  query: str,
                                  max_preview_len: int,
                                  facet_filter) \
            -> T.List[T.Tuple[str, T.Optional[str]]]:
        # language=rst
        """Retrieve documents satisfying some text query.

        Args:
            query: a full text query string. Format may be plugin-specific.
            max_preview_len: the maximum length (in characters) of a text
                preview in the results.
            facet_filter

        Returns:
            a list of tuples, ordered by relevance, with each tuple containing:

            -   the document identifier
            -   a preview of the found texts. If the search engine doesn't
                support this, the list may be empty.

        """


class AbstractBetterStoragePlugin(object):
    # language=rst
    """Specifies the storage API.

    .. warning:: Unused. Work in progress.

    """

    @abc.abstractmethod
    def storage_store(self, data: dict,
                      identifier: T.Optional[str]=None,
                      version:    T.Optional[str]=None) \
            -> T.Tuple[str, str]:
        # language=rst
        """Store a document.

        Args:
            data: the document to store.
            identifier: an identifier by which to reference this document in the
                future.
            version: the last seen version of this document.

        Returns:
            A `tuple` of

                #.  the identifier of the stored document
                #.  the new version number

        Raises:
            KeyError: a document with ``identifier`` exists, but doesn't have
                version ``version``.

        """
        pass

    @abc.abstractmethod
    def storage_retrieve(self, identifier: str) -> T.Tuple[dict, str]:
        # language=rst
        """Retrieve a document by identifier.

        Args:
            identifier: identifier of the document to retrieve.

        Returns:
            A `tuple` of

                #.  the data that was retrieved
                #.  the current version of the document

        Raises:
            KeyError: no document found with ``identifier``.

        """

    @abc.abstractmethod
    def storage_all_ids(self) -> T.Set[str]:
        # language=rst
        """Retrieve all document ids."""

    @abc.abstractmethod
    def storage_all_documents(self) -> T.Mapping[str, dict]:
        # language=rst
        """Retrieve all documents, indexed by ids."""

    @abc.abstractmethod
    def storage_facet_values(self, facet: str, schema: str) -> T.Iterable[T.Any]:
        # language=rst
        """All used values of ``facet`` in all documents with ``schema``.

        Args:
            facet: a json path.
            schema: identifier (ie. module name?) of a schema plugin.

        Returns:
            List of all values found.

        """

    @abc.abstractmethod
    def storage_remove(self, identifier: str, version: T.Optional[str]) -> bool:
        # language=rst
        """Retrieve a document by identifier.

        Args:
            identifier: identifier of the document to remove.
            version: the last seen version of this document.

        Returns:
            ``True`` if the document was found, otherwise ``False``.

        Raises:
            KeyError: document's current version isn't ``version``.

        """
