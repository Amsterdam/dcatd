import typing as T
import abc


class SearchEngine(object):
    # language=rst
    """Fuzzy full text search engine interface."""

    async def fts_index(self, identifier: str, texts: T.Iterable[str]):
        # language=rst
        """Build a full-text search index for a document.

        Args:
            identifier: the identifier of the document from which the texts have
                been extracted.
            texts: the texts extracted from the document.

        """
        pass

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
