FROM python:3.7-slim as builder
    WORKDIR /root/app
    COPY . /root/app
    RUN pip install .

FROM python:3.7-slim
    COPY --from=builder /usr/local/lib/python3.7/site-packages/. /usr/local/lib/python3.7/site-packages
