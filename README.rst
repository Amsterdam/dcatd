.. highlight:: bash

Core of the Data Catalog Project
================================

A microservice with API to store, manage and search through meta data of data
sets.

The latest documentation can always be found at `<https://amsterdam.github.io/dcatd/>`_.


API
---

The API spec can be found at /openapi on a running instance with default settings. The API of the current running instance at Amsterdam can be browsed using `this Swagger UI <https://api.data.amsterdam.nl/api/swagger/?url=/dcatd/openapi>`_.


How to run locally
------------------

Requires Python 3.6.1 or above

Default configuration uses a PostgreSQL database which can be spun up in a container:
Requires Docker and a free port 5433 (this is deliberately another port than PG's default one,
to preempt a collision)

This means you can also change the port to 5432 (and other connection parameters)
in `/examples/running/config.yml` and use a locally running instance of PostgreSQL

Create a virtual environment and install all the dependencies:

::

    make alldeps


Example server
##############

::

    docker-compose up -d database
    make example

See: http://localhost:8000/openapi and http://localhost:8000/datasets

You could even go one further and also spin up the Amsterdam Swagger UI::

    docker-compose up -d database swagger-ui
    make example


Apart from the urls mentioned above you also can
access http://localhost:8686/swagger-ui/?url=http://localhost:8000/openapi

Running tests
#############

::

    docker-compose up -d database
    make test

or

::

    docker-compose up -d database
    make cov


How to run in docker
--------------------

Requires Docker (duh)

Example server
##############

::

    docker-compose up -d

That's it.

See: http://localhost:8001/openapi , http://localhost:8001/datasets
and http://localhost:8686/swagger-ui/?url=http://localhost:8001/openapi

(Example server in docker is accessable through port 8001, while the locally
running example runs on port 8000)

Bootstrap your setup with data
------------------------------

You can import CKAN data into the DCAT-API to bootstrap your install with data

PUT-ting and DELETE-ing data via the API require authorisation.

In the context of Amsterdam City Data can obtiain a JWT from the swagger-ui
(http://localhost:8686/swagger-ui/?url=http://localhost:8000/openapi); export it to JWT:
(For more information see: https://hub.docker.com/r/amsterdam/oauth2swaggerui/ )

::

    export JWT='<JWT>'

Define your local API, and the source CKAN (point to the root of the API of CKAN):

::

    export DCATD='http://localhost:8000/'   # or :8001 , see above
    export CKAN='https://demo.ckan.org/api' # or for instance https://api.data.amsterdam.nl/catalogus/api

Then use the scripts in the utils directory to import data

Remark: this is highly localized for the Amsterdam CKAN instance and will fail beyond the first step
when using CKAN demo data.

Currently this also will fail on the `resources2distributions` step, but you will end up with at least a
somewhat filled database

::

	cd utils

    python dumpckan.py "${CKAN}"
    python ckan2dcat.py "${DCATD}"
    python resources2distributions.py "${DCATD}files" "${JWT}"
    for d in dcatdata/*.json; do
      b=`basename "${d}" '.json'`
      echo -n "${b}..."
      STATUS=$(
        curl --header "Authorization: Bearer ${JWT}" \
          --header "If-None-Match: *" --upload-file "${d}" \
          --silent --output /dev/stderr --write-out "%{http_code}" \
          "${DCATD}datasets/${b}"
      )
      [ "$STATUS" -eq 201 ] && echo "OK" && rm "${d}" || echo "FAILED: $STATUS"
    done


Load production data
--------------------

If you need to load production data  in development you can do the following commands
The first two commands should not be required if database backups would correctly
create the dcatd_latest.gz link. However this is currently not the case. That is
why we need to copy manually with::

    scp admin.datapunt.amsterdam.nl:/mnt/backup_postgres/dcatd_2018-10-30.gz /tmp/
    docker cp  /tmp/dcatd_2018-10-30.gz  dcatd_database_1:/tmp/dcatd_latest.gz


Then we can load it in Postgres with :

    docker-compose exec database update-db.sh dcatd <yourname>


Update documentation
--------------------

Requires Sphinx plus extras:

::

    pip install -e .[docs]


Run the following command to push latest version to github:

::

    make -C sphinx gh-pages

