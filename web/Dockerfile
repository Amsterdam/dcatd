FROM python:3

MAINTAINER datapunt.ois@amsterdam.nl

ENV PYTHONUNBUFFERED 1
EXPOSE 8000

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY * /app/

RUN adduser --system datacatalogus
RUN mkdir -p  /app/data \
    && chown datacatalogus  /app/data

USER datacatalogus
CMD python datacatalogus.py
