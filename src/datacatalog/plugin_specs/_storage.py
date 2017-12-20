import typing as T

from ._markers import hookspecmarker


class Storage(object):
    """Specifies the storage API."""

    @hookspecmarker(firstresult=True)
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

    @hookspecmarker(firstresult=True)
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

    @hookspecmarker(firstresult=True)
    def storage_all_ids(self) -> T.Set[str]:
        # language=rst
        """Retrieve all document ids."""

    @hookspecmarker(firstresult=True)
    def storage_all_documents(self) -> T.Mapping[str, dict]:
        # language=rst
        """Retrieve all documents, indexed by ids."""

    @hookspecmarker
    def storage_facet_values(self, facet: str, schema: str) -> T.Iterable[T.Any]:
        # language=rst
        """All used values of ``facet`` in all documents with ``schema``.

        Args:
            facet: a json path.
            schema: identifier (ie. module name?) of a schema plugin.

        Returns:
            List of all values found.

        """

    @hookspecmarker
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
