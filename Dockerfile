FROM python:3.9-slim as builder
    WORKDIR /root/app
    COPY . /root/app
    RUN pip install .

FROM python:3.9-slim
    COPY --from=builder /usr/local/lib/python3.9/site-packages/. /usr/local/lib/python3.9/site-packages

COPY dcatd.yml /etc/dcatd.yml
