import json
from pathlib import Path
from jsonpointer import resolve_pointer
import pytest
from dcatsync.sync_aschema import sync
from amsterdam_schema import types

HERE = Path(__file__).parent


@pytest.fixture
def patcher(mocker):
    def set_inputs_and_patch(dcat_fn, schema_fn):
        def harvest(token):
            return json.load(open(HERE / "data" / dcat_fn))

        def fetch_schemas(schemas_url):
            schema = types.DatasetSchema.from_file(HERE / "data" / schema_fn)
            return dict(afval=schema)

        mocker.patch("dcatsync.sync_aschema.harvest_dcat_api", harvest)
        mocker.patch("dcatsync.sync_aschema.schema_defs_from_url", fetch_schemas)

        funcs = {}
        for fn in ("add_dataset", "update_dataset", "delete_dataset"):
            funcs[fn] = mocker.patch(f"dcatsync.sync_aschema.{fn}")
        return funcs

    return set_inputs_and_patch


# check which fie is called
@pytest.mark.parametrize(
    "dcat_fn, schema_fn, called",
    [
        ("dcat.json", "afval.json", ("add",)),  # only in incoming
        ("dcat-exist.json", "afval.json", ("update",)),  # existing in dcat
        ("dcat-niet.json", "afval.json", ("add",)),  # niet_beschikbaar in dcat
        ("dcat-two.json", "afval.json", ("delete", "update")),  # afval + dummy in dcat
        ("dcat-two.json", "bommen.json", ("delete", "add")),  # bommen in aschema
        ("dcat-ident.json", "afval.json", ()),  # identical in dcat and aschema
        ("dcat-ident-unsort.json", "afval.json", ()),  # same, but unsorted
        ("dcat-ident-irrelevant.json", "afval.json", ()),  # irrelevant fields in dcat
        ("dcat.json", "afval-niet.json", ()),  # afval aschema niet_beschikbaar
    ],
)
def test_syncing_calls(patcher, dcat_fn, schema_fn, called):
    patched = patcher(dcat_fn, schema_fn)
    sync(False, False)
    called_check = {}
    for fn in patched.keys():
        called_check[fn] = False
    for fn in [f"{fn_prefix}_dataset" for fn_prefix in called]:
        called_check[fn] = True
    for fn in patched.keys():
        assert patched[fn].called == called_check[fn]


# check arguments used when fie is called
@pytest.mark.parametrize(
    "dcat_fn, schema_fn, called, arg_pos, checks",
    [("dcat.json", "afval-more-meta.json", "add", 0, (
        ("/dct:title", "Afvalwegingen"),
        ("/overheidds:doel", "Doelstelling"),
        ("/ams:owner", "De eigenaar"),
        ("/dct:accrualPeriodicity", "dagelijks"),
        ("/dcat:contactPoint/vcard:fn", "Tester"),
        ("/dcat:contactPoint/vcard:hasEmail", "tester@example.com"),
        ("/dct:temporal/time:hasBeginning", "2018-11-13T20:20:39+00:00"),
        ("/dct:temporal/time:hasEnd", "2020-12-31T23:59:59+00:00"),
        ("/dcat:landingPage", "http://example.com"),
        ("/ams:spatialDescription", "Amsterdam"),
        ("/ams:spatialUnit", "na"),
        ("/overheid:grondslag", "De wet"),
    )),],
)
def test_syncing_args(patcher, dcat_fn, schema_fn, called, arg_pos, checks):
    patched = patcher(dcat_fn, schema_fn)
    sync(False, False)
    fie = patched[f"{called}_dataset"]
    for ptr, val in checks:
        assert val == resolve_pointer(fie.call_args.args[arg_pos], ptr, None)
