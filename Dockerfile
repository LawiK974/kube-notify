# Stage 1: Builder stage where the package is built using Poetry
FROM python:3.13.1-alpine3.21 AS builder

ENV PYTHONUNBUFFERED=1 REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
WORKDIR /app
COPY . /app
RUN apk add --no-cache gcc musl-dev libffi-dev git \
    && pip install poetry==1.8.5 pyinstaller==6.11.1 virtualenv==20.28.0 && \
    # Install poetry version plugin see https://github.com/tiangolo/poetry-version-plugin
    poetry self add "poetry-dynamic-versioning[plugin]==v1.4.1" && \
    poetry self add "poetry-pyinstaller-plugin==1.2.1" && \
    # Build the package (this creates the package wheel)
    poetry build

# Stage 2: Lightweight production stage with minimal footprint
FROM busybox:musl

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=builder /app/dist/pyinstaller/*/* /usr/local/bin/
# get necessary libc libraries
COPY --from=builder /lib/ld-musl-*.so.1 /lib/
COPY --from=builder /lib/libz.so.1 /lib/libz.so.1
RUN export ARCH=$(uname -m) && \
    ln -snf "/lib/ld-musl-${ARCH}.so.1" "/lib/libc.musl-${ARCH}.so.1" && \
    chmod a+rx /usr/local/bin/kube-notify && \
    kube-notify --version
LABEL maintainer="Loïc DUBARD <loic97429@gmail.com> @Lawik974"
USER nobody:nobody
ENV PYTHONUNBUFFERED=1 REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
CMD ["/usr/local/bin/kube-notify", "--config", "/app/config.yaml", "--inCluster"]
