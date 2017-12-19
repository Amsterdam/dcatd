FROM python:3

MAINTAINER datapunt.ois@amsterdam.nl

ENV PYTHONUNBUFFERED 1
EXPOSE 8000

WORKDIR /app

RUN pip install --upgrade pip

RUN adduser --system datacatalog
RUN mkdir -p  /app/data \
    && chown datacatalog  /app/data

COPY requirements.txt /app/
COPY config-docker.yml /etc/datacatalog.yml

RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY datacatalog/ /app/datacatalog/

USER datacatalog

CMD python -m datacatalog.web
