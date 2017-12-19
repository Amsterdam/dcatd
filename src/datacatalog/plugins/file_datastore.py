import os
import json

from datacatalog.datastore import AbstractDataStore


class FileDataStore(AbstractDataStore):
    def __init__(self, datastore_config):
        self.FILEDATA_PATH = datastore_config['filedata_path']
        self.LIST_FILE = datastore_config['list_file']
        self.ALL_PACKAGES = datastore_config['all_packages']

        with open(f"{self.FILEDATA_PATH}/{self.ALL_PACKAGES}") as json_data:
            all_packages = json.load(json_data)
            objects = all_packages['result']['results']
            self.packages_by_name = {obj['name']: obj['id'] for obj in objects}

    async def is_healthy(self):
        return os.path.exists(f"{self.FILEDATA_PATH}/{self.LIST_FILE}.json")

    async def get_by_id(self, package_id):
        if package_id in self.packages_by_name:
            package_id = self.packages_by_name[package_id]

        file_path = f"{self.FILEDATA_PATH}/{package_id}.json"
        if os.path.exists(file_path):
            with open(file_path) as json_data:
                return json.load(json_data)
        return None

    async def get_list(self):
        return await self.get_by_id(self.LIST_FILE)


