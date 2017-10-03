import os
import json
import logging

log = logging.getLogger(__name__)


class AbstractDataStore:
    def is_healthy(self):
        pass

    def get_by_id(self, id):
        pass


class FileDataStore(AbstractDataStore):
    FILEDATA_PATH = "/app/data"

    def is_healthy(self):
        return os.path.exists(self.FILEDATA_PATH)

    def get_by_id(self, id):
        file_path = f"{self.FILEDATA_PATH}/{id}.json"
        if os.path.exists(file_path):
            with open(file_path) as json_data:
                return json.load(json_data)
        return None


def is_healthy():
    for datastore in implemented_datastores:
        if not datastore.is_healthy():
            return False
    return True


def get_by_id(id):
    for datastore in implemented_datastores:
        object = datastore.get_by_id(id)
        if object:
            return object
    return None


implemented_datastores = [FileDataStore()]
