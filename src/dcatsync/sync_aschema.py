import os
import datetime
import click
from deepdiff import DeepDiff
from amsterdam_schema.utils import schema_defs_from_url
from amsterdam_schema.types import DatasetSchema
from .utils import (
    get_access_token,
    harvest_dcat_api,
    add_dataset,
    delete_dataset,
    update_dataset,
)


DCAT_URL = os.getenv("DCAT_URL", "http://localhost:8000/")
DCAT_USER = os.getenv("DCAT_USER", "citydata.acc@amsterdam.nl")
DCAT_PASSWORD = os.getenv("DCAT_PASSWORD", "insecure")
SCHEMA_URL = os.getenv("SCHEMA_URL", "https://schemas.data.amsterdam.nl/datasets/")
DSO_URL = os.getenv("DSO_URL", "https://acc.api.data.amsterdam.nl/v1/")


def create_dataset(schema: DatasetSchema):
    ds = {
        "dct:title": schema["title"],
        "dct:description": schema.get("description", ""),
        "dct:source": SCHEMA_URL,
        "ams:status": schema.get("status", "niet_beschikbaar"),
        "dcat:distribution": [],
        "dcat:theme": schema.get("themes", []),
        "dcat:keyword": schema.get("keywords", []),
        "ams:license": "cc-by",
        "overheid:authority": "overheid:Amsterdam",
        "dct:identifier": schema["id"],
        "dct:publisher": {
            "foaf:name": schema.get("publisher") or "OIS/Datapunt",
            "foaf:mbox": "algemeen.OIS@amsterdam.nl",
        },
        "dct:accrualPeriodicity": schema.get("accrualPeriodicity", "unknown"),
        "ams:temporalUnit": schema.get("temporalUnit", "na"),
        "dct:language": schema.get("language", "lang1:nl"),
        "ams:owner": schema.get("owner")
        or "Gemeente Amsterdam, Onderzoek, Informatie en Statistiek",
        "overheidds:doel": schema.get("objective", ""),
        "foaf:isPrimaryTopicOf": {
            "dct:issued": schema.get("dateCreated", ""),
            "dct:modified": schema.get(
                "dateModified", datetime.date.today().isoformat()
            ),
        },
    }

    contact_point = schema.get("contactPoint")
    if contact_point:
        ds["dcat:contactPoint"] = {
            "vcard:fn": contact_point["name"],
            "vcard:hasEmail": contact_point["hasEmail"],
        }

    has_end = schema.get("hasEnd")
    has_beginning = schema.get("hasBeginning")
    if has_beginning and has_end:
        ds["dct:temporal"] = {
            "time:hasBeginning": has_beginning,
            "time:hasEnd": has_end,
        }

    for aschema_name, dcat_name in (
        ("homepage", "dcat:landingPage"),
        ("spatialDescription", "ams:spatialDescription"),
        ("spatialUnit", "ams:spatialUnit"),
        ("spatial", "dct:spatial"),
        ("legalBasis", "overheid:grondslag"),
    ):
        aschema_value = schema.get(aschema_name)
        if aschema_value:
            ds[dcat_name] = aschema_value

    resources = []

    for table in schema.tables:
        resources.append(
            {
                "dct:title": table["id"],
                "dcat:accessURL": f"{DSO_URL}{schema.id}/{table.id}",
                "ams:resourceType": "app",
                "ams:distributionType": "api",
                "ams:serviceType": "rest",
                "ams:classification": "public",
                "dct:license": "cc-by",
                "dct:modified": "",
            }
        )

    ds["dcat:distribution"] = resources

    return ds


@click.command()
@click.option("--dry", is_flag=True, help="Only dry run")
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
def main(dry, verbose):
    sync(dry, verbose)


def sync(dry, verbose):
    access_token = get_access_token(
        DCAT_USER, DCAT_PASSWORD, "localhost" if "localhost" in DCAT_URL else "acc"
    )
    harvested_all = harvest_dcat_api(access_token)
    harvested = list(
        filter(
            lambda ds: ds["ams:status"] != "niet_beschikbaar"
            and ds.get("dct:source", "").startswith(SCHEMA_URL),
            harvested_all["dcat:dataset"],
        )
    )
    harvested_lookup = {ds["dct:title"]: ds for ds in harvested}
    aschemas = {name: aschema for name, aschema in schema_defs_from_url(SCHEMA_URL).items() if aschema.get("status") == "beschikbaar"}
    aschema_lookup = {aschema["title"]: aschema for aschema in aschemas.values()}

    # delete = in old set, not in new schemas
    # add = not in old set, in new schemas
    # update = in old set, in new schemas

    harvested_set = set(harvested_lookup)
    aschema_set = set(aschema_lookup)

    if verbose:
        click.echo(f"Harvested: {harvested_set}")
        click.echo(f"Amsterdam schema: {aschema_set}")
        click.echo(f"Delete: {harvested_set - aschema_set}")
        click.echo(f"Add: {aschema_set - harvested_set}")
        click.echo(f"Update: {aschema_set & harvested_set}")

    if dry:
        return

    for title in harvested_set - aschema_set:
        ds_id = harvested_lookup[title]["dct:identifier"]
        dcat_ds = harvested_lookup[title]
        delete_dataset(ds_id, dcat_ds, access_token)

    for title in aschema_set - harvested_set:
        dcat_ds = create_dataset(aschema_lookup[title])
        add_dataset(dcat_ds, access_token)

    for title in aschema_set & harvested_set:
        ds_id = harvested_lookup[title]["dct:identifier"]
        dcat_ds = create_dataset(aschema_lookup[title])

        # Do a deep compare, only update if needed
        if DeepDiff(
            dcat_ds,
            harvested_lookup[title],
            exclude_regex_paths={
                r".*identif.*",
                r".*modified.*",
                ".*@id",
                ".*ams:purl",
            },
        ):
            update_dataset(ds_id, dcat_ds, access_token)
