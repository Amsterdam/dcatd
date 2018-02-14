FROM python:3.6-alpine3.7
    WORKDIR /root
    RUN apk --update add libpq libuv
    COPY --from=amsterdam/dcatd-builder /root/app/dist/. /root/dist
    COPY --from=amsterdam/dcatd-builder /usr/local/lib/python3.6/site-packages/. /usr/local/lib/python3.6/site-packages
