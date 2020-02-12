import json
from pathlib import Path
import pytest
from attrdict import AttrDict
from dcatsync.sync_aschema import main as sync
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

        funcs = AttrDict()
        for fn in ("add_dataset", "update_dataset", "delete_dataset"):
            funcs[fn] = mocker.patch(f"dcatsync.sync_aschema.{fn}")
        return funcs

    return set_inputs_and_patch


# check which fie is called + with what args
@pytest.mark.parametrize(
    "dcat_fn, schema_fn, called",
    [
        ("dcat.json", "afval.json", ("add",)),
        ("dcat-exist.json", "afval.json", ("update",)),
        ("dcat-niet.json", "afval.json", ("add",)),
        ("dcat-two.json", "afval.json", ("delete", "update")),
        ("dcat-two.json", "bommen.json", ("delete", "add")),
    ],
)
def test_syncing(patcher, dcat_fn, schema_fn, called):
    patched = patcher(dcat_fn, schema_fn)
    sync()
    called_check = {}
    for fn in patched.keys():
        called_check[fn] = False
    for fn in [f"{fn_prefix}_dataset" for fn_prefix in called]:
        called_check[fn] = True
    for fn in patched.keys():
        assert patched[fn].called == called_check[fn]
