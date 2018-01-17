import json
import os

from pkg_resources import resource_stream
import yaml
from aiopluggy import HookimplMarker


hook = HookimplMarker('datacatalog')


class FileStoragePlugin(object):
    # language=rst
    """ Default Datastore implementation.

    This implementation stores all data in files on the local filesystem.

    """

    def __init__(self):
        self.FILEDATA_PATH = None
        self.LIST_FILE = None
        self.ALL_PACKAGES = None
        self.packages_by_name = None

    @hook
    def initialize(self, app):
        # Validate configuration data:
        with resource_stream(__name__, 'file_storage_config_schema.yml') as s:
            schema = yaml.load(s)
        app.config.validate(schema)

        datastore_config = app.config['filedatastore']
        self.FILEDATA_PATH = datastore_config['path']
        self.LIST_FILE = datastore_config['list_file']
        self.ALL_PACKAGES = datastore_config['all_packages']

        with open("{}/{}".format(self.FILEDATA_PATH,
                                      self.ALL_PACKAGES)) as json_data:
            all_packages = json.load(json_data)
            objects = all_packages['result']['results']
            self.packages_by_name = {
                obj['name']: obj['id'] for obj in objects
            }

    @hook
    def health_check(self):
        return self._health_check()

    def _health_check(self):
        if not os.path.exists(
            "{}/{}.json".format(self.FILEDATA_PATH, self.LIST_FILE)
        ):
            return self.__class__

    @hook
    def storage_retrieve(self, id):
        if id in self.packages_by_name:
            id = self.packages_by_name[id]

        file_path = "{}/{}.json".format(
            self.FILEDATA_PATH, id
        )
        if os.path.exists(file_path):
            with open(file_path) as json_data:
                return json.load(json_data)
        return None

    @hook
    def storage_retrieve_list(self):
        return self.storage_retrieve(self.LIST_FILE)


plugin = FileStoragePlugin()
