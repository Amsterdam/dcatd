#!/usr/bin/env bash

set -u # crash on missing env
set -e # stop on any error

# Run from this dir
cd "$(dirname "$0")"

docker-compose build web
docker-compose up --build test
