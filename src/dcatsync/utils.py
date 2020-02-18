import copy
import os
import random
import string
from time import time
from urllib.parse import urlparse, parse_qsl

import requests
import jwt


DCAT_URL = os.getenv("DCAT_URL", "http://localhost:8000/")

_access_token = None


def get_access_token(username, password, environment1):
    if environment1 == "localhost":
        return {}

    global _access_token

    if _access_token is not None:
        decoded = jwt.decode(_access_token, verify=False)
        # We should have more then 100 seconds left
        if int(time()) + 100 > int(decoded["exp"]):
            _access_token = None

    if not _access_token:

        def randomword(length):
            letters = string.ascii_lowercase
            return "".join(random.choice(letters) for i in range(length))

        state = randomword(10)
        scopes = ["CAT/R", "CAT/W"]
        acc_prefix = "acc." if environment1 == "acc" else ""
        authzUrl = f"https://{acc_prefix}api.data.amsterdam.nl/oauth2/authorize"
        params = {
            "idp_id": "datapunt",
            "response_type": "token",
            "client_id": "citydata",
            "scope": " ".join(scopes),
            "state": state,
            "redirect_uri": f"https://{acc_prefix}data.amsterdam.nl/",
        }

        response = requests.get(authzUrl, params, allow_redirects=False)
        if response.status_code == 303:
            location = response.headers["Location"]
        else:
            return {}

        data = {
            "type": "employee_plus",
            "email": username,
            "password": password,
        }

        response = requests.post(location, data=data, allow_redirects=False)
        if response.status_code == 303:
            location = response.headers["Location"]
        else:
            return {}

        response = requests.get(location, allow_redirects=False)
        if response.status_code == 303:
            returned_url = response.headers["Location"]
        else:
            return {}

        # Get grantToken from parameter aselect_credentials in session URL
        parsed = urlparse(returned_url)
        fragment = parse_qsl(parsed.fragment)
        _access_token = fragment[0][1]

    return {"Authorization": "Bearer " + _access_token}


def add_dataset(dataset: dict, access_token: str) -> int:
    url = f"{DCAT_URL}/datasets"
    dataset.pop("dct:identifier", None)
    dataset.pop("@id", None)
    headers = copy.deepcopy(access_token)
    headers["Content-Type"] = "application/json"
    response = requests.post(url, headers=headers, json=dataset)
    if not response:
        print(f"Request error: {response.status_code}")
    return 1 if response else 0


def update_dataset(id1: str, dataset: dict, access_token: str) -> int:
    url = f"{DCAT_URL}/datasets/{id1}"
    response = requests.get(url)
    etag = response.headers["Etag"]
    headers = copy.deepcopy(access_token)
    headers["If-Match"] = etag
    headers["Content-Type"] = "application/json"
    response = requests.put(url, headers=headers, json=dataset)
    if not response:
        print(f"Request error: {response.status_code}")
    return 1 if response else 0


def delete_dataset(id1: str, dataset: dict, access_token: str) -> int:
    dataset["ams:status"] = "niet_beschikbaar"
    return update_dataset(id1, dataset, access_token)


def harvest_dcat_api(access_token):
    url = f"{DCAT_URL}/harvest"
    response = requests.get(url, headers=access_token)
    if not response:
        print(f"Request error: {response.status_code}")
    jsonresponse = response.json()
    return jsonresponse
