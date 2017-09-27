FROM python:3

MAINTAINER datapunt.ois@amsterdam.nl

ENV PYTHONUNBUFFERED 1
EXPOSE 8000

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY * /app/

RUN adduser --system datacatalog
RUN mkdir -p  /app/data \
    && chown datacatalog  /app/data

USER datacatalog
CMD python datacatalog.py
