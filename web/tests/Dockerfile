FROM datacatalog-core:latest

MAINTAINER datapunt.ois@amsterdam.nl

USER root

WORKDIR /app

RUN mkdir -p  /app/tests

COPY * /app/tests/

RUN pip install --no-cache-dir -r tests/requirements.txt

USER datacatalog

CMD pytest
