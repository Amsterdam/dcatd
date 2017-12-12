import logging

from datacatalog.plugin import Plugin, Pluggable

log = logging.getLogger(__name__)


class AbstractSearch(Pluggable):
    async def is_healthy(self):
        pass

    async def search(self, query={}):
        pass


class Search(Plugin):
    def __init__(self, datacatalog_config):
        implementation = datacatalog_config['search']['implementation']
        search_config = datacatalog_config['search']['config']
        super().__init__(implementation, search_config)

    @property
    def implementation(self) -> AbstractSearch:
        return super().implementation
