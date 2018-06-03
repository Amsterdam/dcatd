.. highlight:: bash

Core of the Data Catalog Project
================================

A microservice with API to store, manage and search through meta data of data
sets.

The latest documentation can always be found `here <https://amsterdam.github.io/dcatd/>`_.


API
-----

The API spec can be found at /openapi on a running instance with default settings. The API of the current running instance at Amsterdam can be browsed using Swagger UI `here <https://api.data.amsterdam.nl/api/swagger/?url=/dcatd/openapi>`_.

Contributing
------------------

First create and activate a virtualenv. Then install all dependencies:

::

    make alldeps


Example server
###########

::

    docker-compose up -d database
    make example


Running tests
##########

::

    docker-compose up -d database
    make test

or

::

    docker-compose up -d database
    make cov
