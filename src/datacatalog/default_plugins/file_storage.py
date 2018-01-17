import json
import os

from pkg_resources import resource_stream
import yaml

from datacatalog.plugin_interfaces import AbstractStoragePlugin


class FileStoragePlugin(AbstractStoragePlugin):
    # language=rst
    """ Default Datastore implementation.

    This implementation stores all data in files on the local filesystem.

    """
    def __init__(self, app):
        super().__init__(app)
        datastore_config = app.config['filedatastore']
        self.FILEDATA_PATH = datastore_config['path']
        self.LIST_FILE = datastore_config['list_file']
        self.ALL_PACKAGES = datastore_config['all_packages']

        with open(f"{self.FILEDATA_PATH}/{self.ALL_PACKAGES}") as json_data:
            all_packages = json.load(json_data)
            objects = all_packages['result']['results']
            self.packages_by_name = {obj['name']: obj['id'] for obj in objects}

    async def datastore_is_healthy(self):
        return os.path.exists(f"{self.FILEDATA_PATH}/{self.LIST_FILE}.json")

    async def datastore_get_by_id(self, package_id):
        if package_id in self.packages_by_name:
            package_id = self.packages_by_name[package_id]

        file_path = f"{self.FILEDATA_PATH}/{package_id}.json"
        if os.path.exists(file_path):
            with open(file_path) as json_data:
                return json.load(json_data)
        return None

    async def datastore_get_list(self):
        return await self.datastore_get_by_id(self.LIST_FILE)

    @staticmethod
    def plugin_config_schema():
        with resource_stream(__name__, 'file_storage_config_schema.yml') as s:
            return yaml.load(s)

