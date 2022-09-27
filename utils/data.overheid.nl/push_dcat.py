import json
import os
import re
import urllib
from urllib import request
from urllib.error import HTTPError
import pprint

filetype_prefix = "http://publications.europa.eu/resource/authority/file-type/"

MAP_MEDIATYPE_FORMAT = {
    "text/csv": filetype_prefix + "CSV",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": filetype_prefix
    + "DOCX",
    "application/vnd.geo+json": filetype_prefix + "JSON",
    "application/gml+xml": filetype_prefix + "GML",
    "text/html": filetype_prefix + "HTML",
    "application/json": filetype_prefix + "JSON",
    "application/pdf": filetype_prefix + "PDF",
    "image/png": filetype_prefix + "PNG",
    "application/x-zipped-shp": filetype_prefix + "SHP",
    "application/vnd.ms-excel": filetype_prefix + "XLS",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": filetype_prefix + "XLSX",
    "application/xml": filetype_prefix + "XML",
    "application/octet-stream": filetype_prefix
    + "TAR_XZ",  # How to represent Anders. Format is a required value
}

MAP_LANGUAGE = {
    "lang1:nl": "http://publications.europa.eu/resource/authority/language/NLD",
}

# Map to value in https://waardelijsten.dcat-ap-donl.nl/overheid_license.json
MAP_LICENSES = {
    "cc-by": "http://creativecommons.org/licenses/by/4.0/deed.nl",
    "cc-by-nc": "http://creativecommons.org/licenses/by/4.0/deed.nl",  # ? cc-by-nc missing
    "cc-by-nc-nd": "http://creativecommons.org/licenses/by/4.0/deed.nl",  # ? cc-by-nc-nd missing
    "cc-by-nc-sa": "http://creativecommons.org/licenses/by-sa/4.0/deed.nl",  # ? cc-by-nc-nd missing
    "cc-by-nd": "http://creativecommons.org/licenses/by/4.0/deed.nl",  # ? cc-by-nd missing
    "cc-by-sa": "http://creativecommons.org/licenses/by-sa/4.0/deed.nl",
    "cc-nc": "http://creativecommons.org/publicdomain/mark/1.0/deed.nl",  # ? cc-nc missing
    "cc-zero": "http://creativecommons.org/publicdomain/zero/1.0/deed.nl",
    "other-open": "http://creativecommons.org/publicdomain/mark/1.0/deed.nl",  # ? other-open missing
    "other-by": "http://creativecommons.org/publicdomain/mark/1.0/deed.nl",  # ? other-by missing
    "other-nc": "http://creativecommons.org/publicdomain/mark/1.0/deed.nl",  # ? other-nc missing
    "other-not-open": "http://standaarden.overheid.nl/owms/terms/geslotenlicentie",
    "unspec": "http://standaarden.overheid.nl/owms/terms/licentieonbekend",
}

# Map to https://waardelijsten.dcat-ap-donl.nl/overheid_frequency.json
MAP_FREQUENCY = {
    "unknown": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",
    "realtime": "http://publications.europa.eu/resource/authority/frequency/CONT",
    "day": "http://publications.europa.eu/resource/authority/frequency/DAILY",
    "2pweek": "http://publications.europa.eu/resource/authority/frequency/WEEKLY_2",
    "week": "http://publications.europa.eu/resource/authority/frequency/WEEKLY",
    "2weeks": "http://publications.europa.eu/resource/authority/frequency/WEEKLY_2",
    "month": "http://publications.europa.eu/resource/authority/frequency/MONTHLY",
    "quarter": "http://publications.europa.eu/resource/authority/frequency/QUARTERLY",
    "2pyear": "http://publications.europa.eu/resource/authority/frequency/ANNUAL_2",
    "year": "http://publications.europa.eu/resource/authority/frequency/ANNUAL",
    "2years": "http://publications.europa.eu/resource/authority/frequency/BIENNIAL",
    "4years": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",  # ? does not exist
    "5years": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",
    "10years": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",
    "reg": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",  # ? does not exist
    "irreg": "http://publications.europa.eu/resource/authority/frequency/IRREG",
    "req": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",  # ? does not exist
    "other": "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",
}

# Map themes to : https://standaarden.overheid.nl/owms/terms/TaxonomieBeleidsagenda.xml
MAP_THEMES = {
    "theme:bestuur": "http://standaarden.overheid.nl/owms/terms/Bestuur",
    "theme:bevolking": "http://standaarden.overheid.nl/owms/terms/Sociale_zekerheid",
    "theme:cultuur-en-recreatie": "http://standaarden.overheid.nl/owms/terms/Cultuur_en_recreatie",
    "theme:duurzaamheid-en-milieu": "http://standaarden.overheid.nl/owms/terms/Natuur_en_milieu",
    "theme:economie-en-toerisme": "http://standaarden.overheid.nl/owms/terms/Economie",
    "theme:onderwijs-en-wetenschap": "http://standaarden.overheid.nl/owms/terms/Onderwijs_en_wetenschap",
    "theme:openbare-orde-en-veiligheid": "http://standaarden.overheid.nl/owms/terms/Openbare_orde_en_veiligheid",
    "theme:ruimte-en-topografie": "http://standaarden.overheid.nl/owms/terms/Ruimte_en_infrastructuur",
    "theme:verkeer": "http://standaarden.overheid.nl/owms/terms/Verkeer_(thema)",
    "theme:werk-en-sociale-zekerheid": "http://standaarden.overheid.nl/owms/terms/Werk_(thema)",
    "theme:wonen": "http://standaarden.overheid.nl/owms/terms/Huisvesting_(thema)",
    "theme:zorg-en-welzijn": "http://standaarden.overheid.nl/owms/terms/Zorg_en_gezondheid",
}

MAP_SERVICE_TYPES = {
    "atom": ("application/json", filetype_prefix + "JSON"),
    "rest": ("application/json", filetype_prefix + "JSON"),
    "csw": ("application/gml+xml", filetype_prefix + "XML"),
    "wcs": ("application/octet-stream", filetype_prefix + "TAR_XZ"),
    "wfs": ("application/vnd.geo+json", filetype_prefix + "WFS_SRVC"),
    "wms": ("image/png", filetype_prefix + "WMS_SRVC"),
    "wmts": ("image/png", filetype_prefix + "WMS_SRVC"),
    "soap": ("application/xml", filetype_prefix + "XML"),
    "gpkg": ("application/geopackage+sqlite3", filetype_prefix + "GPKG"),
    "other": ("application/octet-stream", filetype_prefix + "TAR_XZ"),
}


IDENTIFIER_PREFIX = "https://api.data.amsterdam.nl/dcatd/datasets/"


def _to_kebab_case(instr):
    """Used to correct keys for the MAP_LICENSES dict."""
    return instr.replace("_", "-")


def _request_with_headers(url, data=None, method=None, authorization=None):
    headers = {
        "accept": "application/json",
        "accept-charset": "utf-8",
        "user-agent": "Deliberately empty",
    }
    if authorization:
        headers["Authorization"] = authorization
    req = request.Request(url, data=data, method=method)
    for key, val in headers.items():
        req.add_header(key, val)
    return req


def _convert_to_ckan(dcat: dict) -> dict:
    language = MAP_LANGUAGE[dcat["dct:language"]]

    # Remove duplicates and sort for easy comparison
    themes = sorted(list(set([MAP_THEMES[theme] for theme in dcat["dcat:theme"]])))
    tags = [{"name": keyword} for keyword in sorted(list(set(dcat["dcat:keyword"])))]

    if dcat["ams:license"] == "other-not-open":
        access_rights = "http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC"
    elif dcat["ams:license"] == "unspec":
        # If license unknown we have to set access_rights to restricted.
        access_rights = "http://publications.europa.eu/resource/authority/access-right/RESTRICTED"
    else:
        access_rights = "http://publications.europa.eu/resource/authority/access-right/PUBLIC"

    resources = {}
    for dist in dcat["dcat:distribution"]:
        # ? default application/octet-stream if no dcat:mediaType
        mimetype = dist.get("dcat:mediaType", "application/octet-stream")
        format1 = MAP_MEDIATYPE_FORMAT[mimetype]

        if dist["ams:distributionType"] == "api":
            if "ams:serviceType" not in dist:
                print("Missing service type for `distributionType:api`, default to `rest`.")
            types = MAP_SERVICE_TYPES[dist.get("ams:serviceType", "rest")]
            mimetype = types[0]
            format1 = types[1]
        elif dist["ams:distributionType"] == "web":
            mimetype = "text/html"
            format1 = filetype_prefix + "HTML"

        resource = {
            "title": dist["dct:title"],
            "description": dist["description"] if "description" in dist else "unknown",
            "url": dist["dcat:accessURL"],
            # 'resourceType': dist['ams:resourceType'],
            # 'distributionType': dist['ams:distributionType'],
            "mimetype": mimetype,
            "format": format1,
            "name": dist["dct:title"],
            # 'classification':'public', # We only have public datasets in dcat ?
            "size": dist["dcat:byteSize"] if "dcat:byteSize" in dist else None,
            "modification_date": dist["dct:modified"]
            if "dct:modified" in dist
            else dist["foaf:isPrimaryTopicOf"]["dct:modified"],
            "language": [language],  # Inherit from dataset
            "metadata_language": language,  # Inherit from dataset
            "license_id": MAP_LICENSES[_to_kebab_case(dist["dct:license"])],
        }

        # Remove duplicates with the same name or dct:title
        if resource["name"] not in resources:
            resources[resource["name"]] = resource

    ckan = {
        "title": dcat["dct:title"],
        "notes": dcat["dct:description"],
        "dataset_status": f"http://data.overheid.nl/status/{dcat['ams:status']}",
        "owner_org": "gemeente-amsterdam",  # Should there be a relation between owner_org and owner ?
        "resources": list(resources.values()),
        "metadata_language": language,
        "issued": dcat["foaf:isPrimaryTopicOf"]["dct:issued"],
        "modified": dcat["dct:modified"]
        if "dct:modified" in dcat
        else dcat["foaf:isPrimaryTopicOf"]["dct:modified"],
        "frequency": MAP_FREQUENCY.get(
            dcat["dct:accrualPeriodicity"],
            "http://publications.europa.eu/resource/authority/frequency/UNKNOWN",
        ),
        "language": [language],
        "contact_point_name": dcat["dcat:contactPoint"]["vcard:fn"],
        "contact_point_email": dcat["dcat:contactPoint"]["vcard:hasEmail"],
        "publisher": "http://standaarden.overheid.nl/owms/terms/Amsterdam",
        "theme": themes,
        "tags": tags,
        "license_id": MAP_LICENSES[_to_kebab_case(dcat["ams:license"])],
        "authority": "http://standaarden.overheid.nl/owms/terms/" + dcat["overheid:authority"][9:],
        "identifier": IDENTIFIER_PREFIX + dcat["dct:identifier"],
        "name": dcat["dct:identifier"].lower(),
        "source_catalog": "https://data.amsterdam.nl/",
        "access_rights": access_rights,
    }
    return ckan


def dictionary_vary(a: dict, b: dict, exclude: dict, parent_key: str = None) -> bool:
    '''
    Are two dictionaries different. Compare recursively
    Ignore keys in exclude, context dependen on parent key.
    Compare date values only till 8 characters or on date and not time
    '''
    parent_exclude = exclude.get(parent_key, set())

    if set(a.keys()) - parent_exclude != set(b.keys()) - parent_exclude:
        return True

    for key, value in a.items():
        if key not in parent_exclude:
            if isinstance(value, dict):
                if not isinstance(b[key], dict) or dictionary_vary(value, b[key], exclude, key):
                    return True
            elif isinstance(value, list):
                if not isinstance(b[key], list) or len(value) != len(b[key]):
                    return True
                for i in range(len(value)):
                    if isinstance(value[i], dict):
                        if not isinstance(b[key][i], dict) or dictionary_vary(value[i], b[key][i], exclude, key):
                            return True
                    else:  # We do not have lists of lists
                        if value[i] != b[key][i]:
                            return True
            elif key in ('modified', 'modification_date', 'issued', 'dct:issued'):
                if value[:10] != b[key][:10]:
                    return True
            else:
                if value != b[key]:
                    return True

    return False


def push_dcat():
    dcat_env = os.getenv("ENVIRONMENT", "acc")  # acc or prod
    api_key = os.getenv("API_KEY")
    organisation_id = os.getenv("ORGANISATION_ID", "gemeente-amsterdam")

    if dcat_env == "prod":
        dcat_root = "https://api.data.amsterdam.nl/dcatd"
        donl_root = "https://data.overheid.nl/data"
    else:
        dcat_root = "https://acc.api.data.amsterdam.nl/dcatd"
        donl_root = "https://data-acc.overheid.nl/data"

    req = _request_with_headers(f"{dcat_root}/harvest")

    with request.urlopen(req) as response:
        assert 200 == response.getcode()
        datasets_new = json.load(response)
        datasets_new = datasets_new["dcat:dataset"]

    # Get all old datasets for gemeente amsterdam. If we have more then 1000 datasets this should be  changed
    req = _request_with_headers(
        f"{donl_root}/api/3/action/package_search?q=organization:gemeente-amsterdam&rows=1000"
    )
    response = request.urlopen(req)
    assert response.code == 200
    response_dict0 = json.loads(response.read())
    assert response_dict0["success"]
    datasets_old = response_dict0["result"]["results"]
    prefix_len = len(IDENTIFIER_PREFIX)
    identifier_index_map_old = {
        datasets_old[index]["identifier"][prefix_len:]: index for index in range(len(datasets_old))
    }

    identifier_index_map_new = {
        IDENTIFIER_PREFIX + datasets_new[index]["dct:identifier"]: index
        for index in range(len(datasets_new))
    }

    insert_count = 0
    update_count = 0
    delete_count = 0
    count = 0
    remove_resources = {}

    for ds_new in datasets_new:
        identifier = ds_new["dct:identifier"]
        print(f"Processing: {identifier}, {ds_new['dct:title']}")

        owner = ds_new["ams:owner"]
        # Only import datasets where amsterdam is owner
        if not re.search("amsterdam", owner, flags=re.IGNORECASE):
            continue

        # Only import datasets that are beschikbaar
        if ds_new["ams:status"] != "beschikbaar":
            continue

        if not api_key:
            continue

        # if count > 10:
        #    break

        ds_new = _convert_to_ckan(ds_new)

        # check if dataset exists
        ds_old = (
            datasets_old[identifier_index_map_old[identifier]]
            if identifier in identifier_index_map_old
            else None
        )
        if ds_old:
            # Dataset already exists. Use package_update
            # First add ID's to ckan dataset
            id1 = ds_new["id"] = ds_old["id"]

            name_id_map_old = {}
            for res_old in ds_old["resources"]:
                old_name = res_old.get("name")
                if old_name:
                    name_id_map_old[old_name] = res_old["id"]
                old_title = res_old.get("title")
                if old_title:
                    name_id_map_old[old_title] = res_old["id"]

            for res_new in ds_new["resources"]:
                if res_new["name"] in name_id_map_old:
                    res_new["id"] = name_id_map_old[res_new["name"]]
                # else a new id will be assigned

            name_set_new = {res_new["name"] for res_new in ds_new["resources"]}

            # Check if old and new datasets are different
            exclude = {
                None: {
                    "author",
                    "author_email",
                    "basis_register",
                    "changetype",
                    "communities",
                    "creator_user_id",
                    "dataset_quality",
                    "groups",
                    "high_value",
                    "isopen",
                    "license_title",
                    "license_url",
                    "maintainer",
                    "maintainer_email",
                    "metadata_created",
                    "metadata_modified",
                    "national_coverage",
                    "num_resources",
                    "num_tags",
                    "organization",
                    "owner_org",
                    "private",
                    "referentie_data",
                    "revision_id",
                    "state",
                    "type",
                },
                "resources": {
                    "cache_last_updated",
                    "cache_url",
                    "created",
                    "datastore_active",
                    "last_modified",
                    "link_status",
                    "link_status_last_checked",
                    "metadata_created" "metadata_modified",
                    "mimetype_inner",
                    "package_id",
                    "position",
                    "resource_type",
                    "revision_id",
                    "size",
                    "state",
                    "url_type",
                    "webstore_last_updated",
                    "webstore_url",
                },
                "tags": {
                    "display_name",
                    "id",
                    "vocabulary_id",
                    "state",
                },
            }

            # sort tags and themes for easy comparison
            ds_old["tags"] = sorted(ds_old["tags"], key=lambda ds: ds["name"])
            ds_old["theme"] = sorted(ds_old["theme"])

            if not dictionary_vary(ds_new, ds_old, exclude):
                continue

            # Collect resources te be removed
            to_remove = []
            for i in reversed(range(len(ds_old["resources"]))):
                if (
                    ds_old["resources"][i]["name"] not in name_set_new
                    and ds_old["resources"][i]["title"] not in name_set_new
                ):
                    to_remove.append(ds_old["resources"][i]["id"])

            # Remove resource later
            remove_resources[id1] = to_remove

            ds_new_string = urllib.parse.quote(json.dumps(ds_new))
            ds_new_string = ds_new_string.encode("utf-8")
            req.add_header("Content-Length", len(ds_new_string))

            req = _request_with_headers(
                f"{donl_root}/api/3/action/package_update?id={id1}",
                data=ds_new_string,
                authorization=api_key,
                method="POST",
            )
            try:
                response = request.urlopen(req)
            except HTTPError as err:
                if err.code == 409:
                    error_message = err.read()
                    print(error_message)
                    print("Problem with dataset : ")
                    pprint.pprint(ds_new)
                    continue
                else:
                    raise err

            assert response.code == 200
            response_dict2 = json.loads(response.read())
            if response_dict2["success"]:
                update_count += 1

            updated_package = response_dict2["result"]

            count += 1
            # pprint.pprint(updated_package)
        else:
            # Dataset does not exist . Use package_create
            ds_new_string = urllib.parse.quote(json.dumps(ds_new))
            ds_new_string = ds_new_string.encode("utf-8")
            req.add_header("Content-Length", len(ds_new_string))

            req = _request_with_headers(
                f"{donl_root}/api/3/action/package_create",
                data=ds_new_string,
                authorization=api_key,
                method="POST",
            )
            try:
                response = request.urlopen(req)
            except HTTPError as err:
                if err.code == 409 or err.code == 400:
                    error_message = err.read()
                    print(error_message)
                    print("Problem with dataset : ")
                    pprint.pprint(ds_new)
                    continue
                else:
                    raise err

            assert response.code == 200
            response_dict3 = json.loads(response.read())
            if response_dict3["success"]:
                insert_count += 1
            created_package = response_dict3["result"]

            count += 1
            # pprint.pprint(created_package)

    # Delete datasets in datasets_old not in datasets_new
    for ds_old in datasets_old:
        if ds_old["identifier"] not in identifier_index_map_new:
            body = {"id": ds_old["id"]}
            body_string = urllib.parse.quote(json.dumps(body))
            body_string = body_string.encode("utf-8")
            req = _request_with_headers(
                f"{donl_root}/api/3/action/package_delete?id={ds_old['id']}",
                data=body_string,
                authorization=api_key,
                method="POST",
            )
            try:
                response = request.urlopen(req)
            except HTTPError as err:
                error_message = err.read()
                print(error_message)
                raise err

            assert response.code == 200
            response_dict4 = json.loads(response.read())
            if response_dict4["success"]:
                delete_count += 1

    # Delete resources
    delete_res_count = 0
    for ds_id, res_list in remove_resources.items():
        for res_id in res_list:
            body = {"id": res_id}
            body_string = urllib.parse.quote(json.dumps(body))
            body_string = body_string.encode("utf-8")
            req = _request_with_headers(
                f"{donl_root}/api/3/action/resource_delete?id={res_id}",
                data=body_string,
                authorization=api_key,
                method="POST",
            )
            try:
                response = request.urlopen(req)
            except HTTPError as err:
                error_message = err.read()
                print(error_message)
                raise err

            assert response.code == 200
            response_dict5 = json.loads(response.read())
            if response_dict5["success"]:
                delete_res_count += 1

    print(
        f"Datasets inserted:, {insert_count}, Datasets updated: {update_count}, Datasets deleted: {delete_count}, Resources deleted: {delete_res_count}"
    )


if __name__ == "__main__":
    push_dcat()
