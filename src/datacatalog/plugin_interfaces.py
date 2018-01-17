import typing as T
import abc

# from ._storage import *
# from ._search_engine import *
from collections import namedtuple


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


class AbstractSearchPlugin(AbstractPlugin):
    # language=rst
    """ Search plugin definition."""

    @abc.abstractmethod
    async def search_is_healthy(self):
        # language=rst
        """ Health check.

        .. todo:: documentation, signature types

        """

    @abc.abstractmethod
    async def search(self, query: T.Optional[T.Mapping]=None):
        # language=rst
        """ Search.

        .. todo:: documentation, return value type

        """


class AbstractStoragePlugin(AbstractPlugin):
    # language=rst
    """ Datastore plugin definition."""

    @abc.abstractmethod
    async def datastore_is_healthy(self):
        # language=rst
        """ Health check.

        .. todo:: documentation, signature types

        """

    @abc.abstractmethod
    async def datastore_get_by_id(self, id):
        # language=rst
        """ get by id.

        .. todo:: documentation, return value type

        """

    @abc.abstractmethod
    async def datastore_get_list(self):
        # language=rst
        """ get list.

        .. todo:: documentation, return value type

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


Plugins = namedtuple('Plugins', ['datastore', 'search'])
ALL_INTERFACES = Plugins(AbstractStoragePlugin, AbstractSearchPlugin)


def implemented_interfaces(plugin):
    for name in Plugins._fields:
        klass = getattr(ALL_INTERFACES, name)
        if isinstance(plugin, klass) or klass.implemented_by(plugin):
            yield name
