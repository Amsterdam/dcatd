import os
import json
import logging

log = logging.getLogger(__name__)


class AbstractDataStore:
    async def is_healthy(self):
        pass

    async def get_by_id(self, id):
        pass

    async def get_list(self):
        pass


class FileDataStore(AbstractDataStore):
    FILEDATA_PATH = "/app/data"
    LIST_FILE = "package_list"
    ALL_PACKAGES = "packages.json"

    def __init__(self):
        with open(f"{self.FILEDATA_PATH}/{self.ALL_PACKAGES}") as json_data:
            all_packages = json.load(json_data)
            objects = all_packages['result']['results']
            self.packages_by_name = {obj['name']: obj['id'] for obj in objects}

    async def is_healthy(self):
        return os.path.exists(f"{self.FILEDATA_PATH}/{self.LIST_FILE}.json")

    async def get_by_id(self, id):
        if id in self.packages_by_name:
            id = self.packages_by_name[id]

        file_path = f"{self.FILEDATA_PATH}/{id}.json"
        if os.path.exists(file_path):
            with open(file_path) as json_data:
                return json.load(json_data)
        return None

    async def get_list(self):
        return await self.get_by_id(self.LIST_FILE)


async def is_healthy():
    for datastore in implemented_datastores:
        if not await datastore.is_healthy():
            return False
    return True


async def get_by_id(id):
    for datastore in implemented_datastores:
        data_object = await datastore.get_by_id(id)
        if data_object:
            return data_object
    return None


async def get_list():
    results = []
    for datastore in implemented_datastores:
        list = await datastore.get_list()
        results.append(list)
    return results

implemented_datastores = [FileDataStore()]
