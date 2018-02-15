FROM python:3.6-alpine3.7 as builder
    WORKDIR /root/app
    COPY . /root/app
    RUN apk --update add postgresql-dev python3-dev build-base
    RUN python setup.py sdist
    RUN pip install .
    RUN pip install --user .[test]

FROM python:3.6-alpine3.7
    WORKDIR /root
    RUN apk --update add libpq libuv
    COPY --from=builder /root/app/dist/. /root/dist
    COPY --from=builder /usr/local/lib/python3.6/site-packages/. /usr/local/lib/python3.6/site-packages
