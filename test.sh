#!/usr/bin/env bash

set -u # crash on missing env
set -e # stop on any error

# Run from this dir
cd "$(dirname "$0")"

docker-compose -f docker-compose-for-tests.yml build web
docker-compose -f docker-compose-for-tests.yml up --build test
