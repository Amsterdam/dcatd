FROM python:3.6-alpine
MAINTAINER datapunt@amsterdam.nl

EXPOSE 8000

WORKDIR /app

COPY * /app/

RUN pip3 install --no-cache-dir .

USER datapunt
ENTRYPOINT ["uwsgi"]