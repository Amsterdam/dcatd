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

How to run
----------

Open a terminal in the root-dir of this project and type::

    docker-compose up -d

Now you can point your browser at `http://localhost:8000/
<http://localhost:8000/>`_ and see content served by the code.


How to run tests
----------------

Run the script in the :file:`test` folder (that utilizes the
:file:`docker-compose-for-tests.yml`)::

    ./test.sh

To do: make locally testing possible

