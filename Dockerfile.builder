FROM python:3.6-alpine3.7
    WORKDIR /root/app
    COPY . /root/app
    RUN apk --update add postgresql-dev python3-dev build-base
    RUN python setup.py sdist
    RUN pip install .
    RUN pip install --user .[test]
