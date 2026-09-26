FROM python:3.13-alpine

# cups-client provides /usr/bin/lp.
RUN apk add --no-cache cups-client \
	&& adduser -D -H -u 10001 print

WORKDIR /app
COPY print_api.py /app/print_api.py
RUN chown -R print:print /app

USER print
EXPOSE 6320
ENV PRINT_API_BIND=0.0.0.0 \
	PRINT_API_PORT=6320

ENTRYPOINT ["python3", "/app/print_api.py"]
