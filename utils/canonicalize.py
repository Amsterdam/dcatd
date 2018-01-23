import json
import sys

json.dump(json.load(sys.__stdin__), sys.__stdout__, indent=2, sort_keys=True)
