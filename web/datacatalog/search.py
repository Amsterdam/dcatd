import os
import json
import logging

log = logging.getLogger(__name__)


class AbstractSearch:
    def is_healthy(self):
        pass

    def search(self, query={}):
        pass


class InMemorySearch(AbstractSearch):
    FILEDATA_PATH = "/app/data/packages.json"

    def __init__(self):
        if self.is_healthy():
            with open(self.FILEDATA_PATH) as json_data:
                self.all_packages = json.load(json_data)

    def is_healthy(self):
        return os.path.exists(self.FILEDATA_PATH)

    def search(self, query={}):
        return self.all_packages


def is_healthy():
    return implemented_serach.is_healthy()


def search(query={}):
    return implemented_serach.search(query)


implemented_serach = InMemorySearch()
