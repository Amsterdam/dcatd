import time

from os import path

from aiohttp import FormData
from aiohttp.test_utils import unittest_run_loop
from mockito import when, unstub, any
from jwcrypto.jwt import JWT

from datacatalog.plugins import postgres as pgpl, swift
from datacatalog.jwks import get_keyset
from tests.datacatalog.base_test_case import BaseTestCase


# Note: the valid token relies on the key in the default config.yml
_INVALID_TOKEN = "bearer invalid_token"

_SUT_DOC_ID = '_FlXXpXDa-Ro3Q'


def create_valid_token(app, subject, scopes):
    jwks = get_keyset()
    assert len(jwks) > 0

    key = next(iter(jwks['keys']))
    now = int(time.time())

    header = {
        'alg': 'ES256',  # algorithm of the test key
        'kid': key.key_id
    }

    token = JWT(
        header=header,
        claims={
            'iat': now,
            'exp': now + 600,
            'scopes': scopes,
            'subject': subject
        })
    token.make_signed_token(key)
    return 'bearer ' + token.serialize()


class DatasetTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.admin_token = create_valid_token(self.app, 'test@test.nl', ['CAT/W', 'CAT/R'])
        self.redact_token = create_valid_token(self.app, 'test@test.nl', ['CAT/R'])


    @unittest_run_loop
    async def test_succesfull_start(self):
        for endpoint, expected_text in [
            ("/datasets", '"dcat:dataset":[]'),
            ("/openapi", '"openapi": "3.0.0"'),
            ("/system/health", "systemhealth is OK"),
        ]:
            response = await self.client.request("GET", endpoint)
            text = await response.text()
            self.assertEqual(response.status, 200)
            self.assertIn(expected_text, text)

    @unittest_run_loop
    async def test_dataset_operations(self):
        with open(self._WORKING_PATH + path.sep + 'test.json') as definition:
            data = definition.read()

        with open(self._WORKING_PATH + path.sep + 'test_update.json') as defn:
            updated_data = defn.read()

        with open(self._WORKING_PATH + path.sep + 'test_unpublished.json') as defn:
            unpublished_data = defn.read()

        basic_headers = {
            'origin': 'http://localhost',
            'Access-Control-Request-Method': 'POST',
            'content-type': 'application/json',
            'authorization': self.admin_token
        }

        admin_headers = {**basic_headers}
        invalid_headers = {**basic_headers, **{'authorization': _INVALID_TOKEN}}

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=invalid_headers)

        self.assertEqual(response.status, 400, 'Verkeerde reactie op verkeer token')

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=admin_headers)

        self.assertEqual(response.status, 201, 'Toevoegen dataset mislukt')

        etag = response.headers.get('Etag')

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=admin_headers)

        self.assertEqual(
            response.status, 400, 'Geen 400 error bij duplicate entry')

        response = await self.client.request(
            "GET", f"/datasets/{_SUT_DOC_ID}")

        self.assertEqual(response.headers.get('Etag'), etag,
                          'Etag is veranderd')

        response = await self.client.request(
            "GET", f"/datasets/{_SUT_DOC_ID}", headers={'If-None-Match': etag})

        self.assertEqual(
            response.status, 304,
            'Geen geldige response voor If-none-match request ontvangen')

        response = await self.client.request(
            "GET", f"/datasets/{_SUT_DOC_ID}",
            headers={'If-None-Match': 'notanetag'})

        self.assertNotEqual(response.status, 304, 'Onterechte not modified ontvangen')

        response = await self.client.request(
            "GET", f"/datasets", params={'q': 'nonexistent'})

        self.assertEqual(response.status, 200, 'Geen match resulteert in !200 state')

        response_json = await response.json()

        self.assertEqual(response_json['dcat:dataset'], [], 'Leeg resultaat verwacht')

        response = await self.client.request(
            "GET", f"/datasets", params={'q': 'ouderen'})

        response_json = await response.json()

        self.assertEqual(
            response_json['dcat:dataset'][0]['dct:description'],

            'Lijsten en locaties van verschillende zorgvoorzieningen voor '
            'ouderen in\nAmsterdam: verpleeg- en verzorgingshuizen, zorg en '
            'hulp bij dementie en\ndienstencentra voor ouderen',

            'Ander resultaat verwacht'
        )

        response = await self.client.request(
            "PUT", f"/datasets/{_SUT_DOC_ID}",
            headers={**admin_headers, **{'If-Match': 'random'}},
            data=updated_data)

        self.assertEqual(response.status, 400, '')

        response = await self.client.request(
            "DELETE", f"/datasets/{_SUT_DOC_ID}",
            headers={**admin_headers, **{'If-Match': 'random'}})

        self.assertEqual(response.status, 400, 'Document onterecht verwijderd')

        response = await self.client.request(
            "DELETE", f"/datasets/{_SUT_DOC_ID}",
            headers={**admin_headers, **{'If-Match': etag}})

        self.assertEqual(response.status, 204, 'Document kon niet worden verwijderd')

        # Check redact access on POST
        redact_headers = {**basic_headers, **{'authorization': self.redact_token}}

        response = await self.client.request(
            "POST", "/datasets", data=data, headers=redact_headers)

        self.assertEqual(response.status, 403, 'Redacteur mag dataset publiceren')

        response = await self.client.request(
            "POST", "/datasets", data=unpublished_data, headers=redact_headers)

        self.assertEqual(response.status, 201, 'Redacteur mag niet beschikbare dataset niet opslaan')

        etag = response.headers.get('Etag')

        # Check redact access on PUT
        response = await self.client.request(
            "PUT", f"/datasets/{_SUT_DOC_ID}",
            headers={**redact_headers, **{'If-Match': 'random'}},
            data=data)

        self.assertEqual(response.status, 403, 'Redacteur mag dataset publiceren')

        response = await self.client.request(
            "PUT", f"/datasets/{_SUT_DOC_ID}",
            headers={**redact_headers, **{'If-Match': etag}},
            data=unpublished_data)

        self.assertEqual(response.status, 204, 'Redacteur mag ongepubliceerde dataset niet opslaan')

    @unittest_run_loop
    async def testUpload(self):
        headers = {
            'Accept': "application/json",
            'Authorization': self.redact_token,
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

        self.assertEqual(response.status, 201, 'File upload mislukt')

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
