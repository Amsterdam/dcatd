FROM python:3.6-slim as builder
    WORKDIR /root/app
    COPY . /root/app
    RUN pip install .

FROM python:3.6-slim
    COPY --from=builder /usr/local/lib/python3.6/site-packages/. /usr/local/lib/python3.6/site-packages
