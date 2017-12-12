import logging

from datacatalog.plugin import Plugin, Pluggable

log = logging.getLogger(__name__)


class AbstractDataStore(Pluggable):
    async def is_healthy(self):
        pass

    async def get_by_id(self, id):
        pass

    async def get_list(self):
        pass


class DataStore(Plugin):
    def __init__(self, datacatalog_config):
        implementation = datacatalog_config['datastore']['implementation']
        datastore_config = datacatalog_config['datastore']['config']
        super().__init__(implementation, datastore_config)

    @property
    def implementation(self) -> AbstractDataStore:
        return super().implementation
