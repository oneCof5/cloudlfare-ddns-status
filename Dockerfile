FROM python:3.12-alpine

LABEL org.opencontainers.image.source=https://github.com/oneCof5/cloudflare-ddns-status

RUN apk add --no-cache bash jq tzdata

WORKDIR /app

COPY app.py /app/app.py
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh \
 && mkdir -p /data /out

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]