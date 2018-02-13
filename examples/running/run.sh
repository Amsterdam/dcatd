#!/usr/bin/env bash

cd "$(dirname "${0}")"

export CONFIG_PATH=./config.yml
exec python3 main.py
