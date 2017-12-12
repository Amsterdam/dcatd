#!/usr/bin/env bash

set -u # crash on missing env
set -e # stop on any error

# Run from this dir
cd "$(dirname "$0")"

pip install -r web/tests/requirements.txt
pytest
pip uninstall -y -r web/tests/requirements.txt
