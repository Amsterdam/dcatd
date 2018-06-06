from os import path

from aiohttp import FormData
from aiohttp.test_utils import unittest_run_loop
from mockito import when, unstub, any

from datacatalog.plugins import postgres as pgpl, swift
from tests.datacatalog.base_test_case import BaseTestCase

# Note: the valid token relies on the key in the default config.yml
_INVALID_TOKEN = "bearer invalid_token"
_VALID_TOKEN = "bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjJhZW" \
               "RhZmJhLTgxNzAtNDA2NC1iNzA0LWNlOTJiN2M4OWNjNiJ9.eyJzY29wZX" \
               "MiOlsiQ0FUL1ciXX0.IJC_0ElBuHEPOcmn0ucUzs4313Rac93Ki4F38u_" \
               "h9_rIkl_S_oqi72TtTLCZeO3XE7OZXgyHKXFH8JCZMh8pVQ"

_SUT_DOC_ID = '_FlXXpXDa-Ro3Q'


class DatasetTestCase(BaseTestCase):
    @unittest_run_loop
    async def test_succesfull_start(self):
        preflight_headers = {
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'origin, random_header_name',
            'Origin': 'http://localhost'
        }
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

        with open(
                self._WORKING_PATH + path.sep + 'test_update.json') as defn:
            updated_data = defn.read()

        basic_headers = {
            'origin': 'http://localhost',
            'Access-Control-Request-Method': 'POST',
            'content-type': 'application/json',
            'authorization': _VALID_TOKEN
        }

        valid_headers = {**basic_headers, **{'authorization': _VALID_TOKEN}}
        invalid_headers = {**basic_headers, **{'authorization': _INVALID_TOKEN}}

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=invalid_headers)

        self.assertEquals(response.status, 400,
                          'Verkeerde reactie op verkeer token')

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=valid_headers)

        self.assertEquals(response.status, 201, 'Toevoegen dataset mislukt')

        etag = response.headers.get('Etag')

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=valid_headers)

        self.assertEquals(
            response.status, 400, 'Geen 400 error bij duplicate entry')

        response = await self.client.request(
            "GET", f"/datasets/{_SUT_DOC_ID}")

        self.assertEquals(response.headers.get('Etag'), etag,
                          'Etag is veranderd')

        response = await self.client.request(
            "GET", f"/datasets/{_SUT_DOC_ID}", headers={'If-None-Match': etag})

        self.assertEquals(
            response.status, 304,
            'Geen geldige response voor If-none-match request ontvangen')

        response = await self.client.request(
            "GET", f"/datasets/{_SUT_DOC_ID}",
            headers={'If-None-Match': 'notanetag'})

        self.assertNotEquals(response.status, 304,
                             'Onterechte not modified ontvangen')

        response = await self.client.request(
            "GET", f"/datasets", params={'q': 'nonexistent'})

        self.assertEquals(response.status, 200,
                          'Geen match resulteert in !200 state')

        response_json = await response.json()

        self.assertEquals(response_json['dcat:dataset'], [],
                          'Leeg resultaat verwacht')

        response = await self.client.request(
            "GET", f"/datasets", params={'q': 'ouderen'})

        response_json = await response.json()

        self.assertEquals(
            response_json['dcat:dataset'][0]['dct:description'],

            'Lijsten en locaties van verschillende zorgvoorzieningen voor '
            'ouderen in\nAmsterdam: verpleeg- en verzorgingshuizen, zorg en '
            'hulp bij dementie en\ndienstencentra voor ouderen',

            'Ander resultaat verwacht'
        )

        response = await self.client.request(
            "PUT", f"/datasets/{_SUT_DOC_ID}",
            headers={**valid_headers, **{'If-Match': 'random'}},
            data=updated_data)

        self.assertEquals(response.status, 400, '')

        response = await self.client.request(
            "DELETE", f"/datasets/{_SUT_DOC_ID}",
            headers={**valid_headers, **{'If-Match': 'random'}})

        self.assertEquals(response.status, 400, 'Document onterecht verwijderd')

        response = await self.client.request(
            "DELETE", f"/datasets/{_SUT_DOC_ID}",
            headers={**valid_headers, **{'If-Match': etag}})

        self.assertEquals(response.status, 204,
                          'Document kon niet worden verwijderd')

    @unittest_run_loop
    async def testUpload(self):
        headers = {
            'Accept': "application/json",
            'Authorization': _VALID_TOKEN,
            'Cache-Control': "no-cache",
        }

        async def returner(value):
            return value

        client = self.client

        when(swift)._put_file_to_object_store(
            any(str),
            'application/json',
            any,
            filename='test_upload.json').thenReturn(returner("randomness"))

        with open(self._WORKING_PATH + path.sep + 'test.json', 'rb') as file:
            data = FormData()
            data.add_field('distribution', file,
                           filename='test_upload.json',
                           content_type='application/json')

            response = await client.post(
                path='/files',
                data=data,
                headers=headers)

        unstub()

        self.assertEquals(response.status, 201, 'File upload mislukt')

    def tearDown(self):
        async def cleanup():
            try:
                _, etag = await pgpl.storage_retrieve(
                    app=self.app, docid=_SUT_DOC_ID)
            except KeyError:
                # Nothing to clean
                return

            if etag:
                await pgpl.storage_delete(
                    app=self.app, docid=_SUT_DOC_ID, etags={etag})

        self.loop.run_until_complete(cleanup())
