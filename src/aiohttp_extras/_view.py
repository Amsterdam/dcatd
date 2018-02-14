import logging
import re
import typing as T

from aiohttp import web
from multidict import MultiDict

_logger = logging.getLogger(__name__)

_GET_IN_PROGRESS = 'aiohttp_extras.GET_IN_PROGRESS'


def _slashify(s):
    assert isinstance(s, str)
    return s if s.endswith('/') else s + '/'


class View(web.View):

    def __init__(
        self,
        request: web.Request,
        match_dict: T.Optional[T.Mapping[str, str]]=None,
        *args, **kwargs
    ):
        super().__init__()
        if match_dict is None:
            rel_url = request.rel_url
        else:
            rel_    url = self.aiohttp_resource().url_for(**match_dict)
        self.__rel_url = rel_url
        self.__embed = None
        self.__query = None
        self.__canonical_rel_url = None
        self.__match_dict = dict(
            # Ugly: we're using non-public member ``_match()`` of
            # :class:`aiohttp.web.Resource`.  But most alternatives are
            # equally ugly.
            self.aiohttp_resource()._match(self.rel_url.raw_path)
        )

    def __getitem__(self, item):
        # language=rst
        """Shorthand for :meth:`self.match_dict[item] <match_dict>`"""
        return self.__match_dict[item]

    @property
    def match_dict(self):
        # language=rst
        """

        Todo:
            Add documentation, explaining the difference between this method and
            :attr:`self.request.match_info <aiohttp.web.Request.match_info>`.

        """
        return self.__match_dict if self.__match_dict is not None else self.request.match_info

    @match_dict.setter
    def match_dict(self, value):
        self.__match_dict = dict(value)

    @property
    def rel_url(self) -> web.URL:
        # language=rst
        """The relative URL as passed to the constructor."""
        return self.__rel_url

    @property
    def canonical_rel_url(self) -> web.URL:
        # language=rst
        """Like :meth:`rel_url`, but with all default query parameters explicitly listed."""
        if self.__canonical_rel_url is None:
            self.__canonical_rel_url = self.__rel_url.with_query(self.query)
        # noinspection PyTypeChecker
        return self.__canonical_rel_url

    @property
    def query(self):
        # language=rst
        """Like ``self.rel_url.query``, but with default parameters added.

        These default parameters are retrieved from the swagger definition.

        """
        if self.__query is None:
            self.__query = MultiDict(self.default_query_params)
            self.__query.update(self.__rel_url.query)
        return self.__query

    @property
    def default_query_params(self) -> T.Dict[str, str]:
        return {}

    @classmethod
    def add_to_router(cls,
                      router: web.UrlDispatcher,
                      path: str,
                      expect_handler: T.Callable=None):
        # language=rst
        """Adds this View class to the aiohttp router."""
        cls._aiohttp_resource = router.add_resource(path)
        # Register the current class in the appropriate registry:
        # if isinstance(cls._aiohttp_resource, web.DynamicResource):
        #     View.PATTERNS[cls._aiohttp_resource.get_info()['pattern']] = cls
        # elif isinstance(cls._aiohttp_resource, web.PlainResource):
        #     View.PATHS[cls._aiohttp_resource.get_info()['path']] = cls
        # else:
        #     _logger.critical("aiohttp router method 'add_resource()' returned resource object of unexpected type %s", cls._aiohttp_resource.__class__)
        if (
            not isinstance(cls._aiohttp_resource, web.DynamicResource) and
            not isinstance(cls._aiohttp_resource, web.PlainResource)
        ):
            _logger.critical("aiohttp router method 'add_resource()' returned resource object of unexpected type %s", cls._aiohttp_resource.__class__)
        cls._aiohttp_resource.rest_utils_class = cls
        cls._aiohttp_resource.add_route('*', cls, expect_handler=expect_handler)
        return cls._aiohttp_resource

    @classmethod
    def aiohttp_resource(cls) -> T.Union[web.PlainResource, web.DynamicResource]:
        try:
            return cls._aiohttp_resource
        except AttributeError:
            raise Exception(
                f"{cls!s}.aiohttp_resource() called before {cls!s}.add_to_router()"
            )

    async def get(self) -> web.StreamResponse:
        if _GET_IN_PROGRESS in self.request:
            raise web.HTTPInternalServerError()
        self.request[_GET_IN_PROGRESS] = True

        if self.request.method == 'GET':
            data = await self.to_json()
        response = web.StreamResponse()
        if isinstance(await self.etag(), str):
            response.headers.add('ETag', await self.etag())
        response.content_type = self.best_content_type
        response.enable_compression()
        if str(self.canonical_rel_url) != str(self.request.rel_url):
            response.headers.add('Content-Location', str(self.canonical_rel_url))
        await response.prepare(self.request)
        if self.request.method == 'GET':
            pass  # TODO: implement.
        response.write_eof()
        del self.request[_GET_IN_PROGRESS]
        return response

    async def head(self):
        return await self.get()

