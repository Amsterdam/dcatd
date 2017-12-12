.. highlight:: bash

Core of the Data Catalog Project
================================

A microservice with API to store, manage and search through meta data of data
sets.


Requirements
------------

All requirements have been abstracted away using `Docker
<https://www.docker.com/>`_.

If you want to roll your own runtime environment, the :file:`Dockerfile`(s) and
:file:`docker-compose.yml` should provide you with sufficient information to
create an environment in which to run the service.

How to run in Docker
--------------------

Open a terminal in the root-dir of this project and type::

    docker-compose up -d

Now you can point your browser at `http://localhost:8000/
<http://localhost:8000/>`_ and see content served by the code.


How to run tests in Docker
--------------------------

Run the script (that utilizes the
:file:`docker-compose-for-tests.yml`)::

    ./test.sh

How to run locally
------------------

The source requires Python 3.6, make sure have that installed.
Create and activate a virtualenv and then run the following commands from the root-directory of the project::

    pip install -r web/requirements.txt
    PYTHONPATH=./web python3 -m datacatalog.web

Now you can point your browser at `http://localhost:8000/
<http://localhost:8000/>`_ and see content served by the code.

How to run tests locally
------------------------

The following instructions asume you have a virtualenv activated
in which the project successfully runs (see previous section).

Then run the script::

    ./test-local.sh


