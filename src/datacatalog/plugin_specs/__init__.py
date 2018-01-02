import typing as T
import abc

# from ._storage import *
# from ._search_engine import *
from collections import namedtuple


class AbstractPlugin(abc.ABC):

    @classmethod
    def __subclasscheck__(cls, klass) -> bool:
        # language=rst
        """

        Returns:
            ``True`` if ``klass`` implements all abstact methods in ``cls``.
            Otherwise, the normal algorithm for subclass detection is invoked,
            which will probably return ``False``.

        """
        if abc.ABCMeta.__subclasscheck__(cls, klass):
            return True
        return all(
            hasattr(klass, abstract_method_name)
            for abstract_method_name in cls.__abstractmethods__
        )


class AbstractSearch(AbstractPlugin):
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


class AbstractDatastore(AbstractPlugin):
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


Plugins = namedtuple('Plugins', ['datastore', 'search'])
ALL_INTERFACES = Plugins(AbstractDatastore, AbstractSearch)


def implemented_interfaces(plugin):
    for name in Plugins._fields:
        klass = getattr(ALL_INTERFACES, name)
        if isinstance(plugin, klass):
            yield name
