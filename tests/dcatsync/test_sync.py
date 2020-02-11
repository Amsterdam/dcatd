import json
from pathlib import Path
from dcatsync import utils
from dcatsync.sync_aschema import main
from amsterdam_schema import utils as asutils

HERE = Path(__file__).parent


def test_syncing(when):
    when(utils).harvest_dcat_api(...).thenReturn(
        json.load(open(HERE / "data" / "dcat.json"))
    )
    when(asutils).schema_defs_from_url(...).thenReturn({})

    main()


