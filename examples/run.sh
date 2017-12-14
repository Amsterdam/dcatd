#!/usr/bin/env bash

cd "$(dirname "${0}")"
echo "$(echo -n "${0}")"

export CONFIG_PATH=./config.yml
exec python3 main.py
