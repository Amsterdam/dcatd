FROM datacatalog-core:latest

MAINTAINER datapunt.ois@amsterdam.nl

USER root

WORKDIR /app

RUN mkdir -p  /app/tests

COPY requirements.txt /app/tests/requirements.txt
RUN pip install --no-cache-dir -r tests/requirements.txt

COPY * /app/tests/

USER datacatalog

CMD pytest
