import os

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from datacatalog.plugins import postgres as pgpl
from os import path

from datacatalog import application


class GenericDcatdTestCase(AioHTTPTestCase):

    # Note: the valid token relies on the key in the default config.yml
    _INVALID_TOKEN = "bearer invalid_token"
    _VALID_TOKEN = "bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjJhZW" \
                   "RhZmJhLTgxNzAtNDA2NC1iNzA0LWNlOTJiN2M4OWNjNiJ9.eyJzY29wZX" \
                   "MiOlsiQ0FUL1ciXX0.IJC_0ElBuHEPOcmn0ucUzs4313Rac93Ki4F38u_" \
                   "h9_rIkl_S_oqi72TtTLCZeO3XE7OZXgyHKXFH8JCZMh8pVQ"

    _WORKING_PATH = path.dirname(path.abspath(__file__))

    async def get_application(self):
        os.environ['CONFIG_PATH'] = self._WORKING_PATH + \
                                    path.sep + 'integration_config.yml'
        return application.Application()

    @unittest_run_loop
    async def test_succesfull_start(self):
        for endpoint, expected_text in [
            ("/datasets", '"dcat:dataset":[]'),
            ("/openapi", '"openapi": "3.0.0"'),
            ("/system/health", "systemhealth is OK"),
        ]:
            response = await self.client.request("GET", endpoint)
            text = await response.text()
            self.assertEquals(response.status, 200)
            self.assertIn(expected_text, text)

    @unittest_run_loop
    async def test_dataset_operations(self):
        with open(self._WORKING_PATH + path.sep + 'test.json') as definition:
            data = definition.read()

        valid_headers = {
            'origin': 'http://localhost',
            'Access-Control-Request-Method': 'POST',
            'content-type': 'application/json',
            'authorization': self._VALID_TOKEN
        }

        docid = '_FlXXpXDa-Ro3Q'

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=valid_headers)

        self.assertEquals(response.status, 201, 'Toevoegen dataset mislukt')

        etag = response.headers.get('Etag')

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=valid_headers)

        self.assertEquals(
            response.status, 400, 'Geen 400 error bij duplicate entry')

        response = await self.client.request(
            "GET", f"/datasets/{docid}")

        self.assertEquals(response.headers.get('Etag'), etag, 'Etag is veranderd')

        response = await self.client.request(
            "GET", f"/datasets/{docid}", headers={'If-None-Match': etag})

        self.assertEquals(response.status, 304, 'Geen geldige response voor If-none-match request ontvangen')

        await pgpl.storage_delete(docid, {etag})

    @unittest_run_loop
    async def test_dataset_listing(self):
        response = await self.client.request("GET", "/datasets")
        await response.text()
        self.assertEquals(response.status, 200)

    ## Test dataset
    #Test querying datasets
    #Test adding a dataset
    #Test removing a dataset

    ## Authentication
    #Skip for now

    ##
    # Etag responses

    ## Test files
    #Test adding a file
    #Test reading back a file
    #Test removing a file


    # 0 = {PlainResource} <PlainResource  /datasets
    # 1 = {DynamicResource} <DynamicResource  /datasets/{dataset}
    # 2 = {PlainResource} <PlainResource  /openapi
    # 3 = {PlainResource} <PlainResource  /system/health
    # 4 = {PlainResource} <PlainResource  /files
