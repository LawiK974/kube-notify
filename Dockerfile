# Stage 1: Builder stage where the package is built using Poetry
FROM python:alpine AS builder

ENV PYTHONUNBUFFERED=1 REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
WORKDIR /app
COPY . /app
RUN apk add --no-cache gcc musl-dev libffi-dev git \
    && pip install poetry==1.8.3 pyinstaller==6.8.0 virtualenv==20.26.2 && \
    # Install poetry version plugin see https://github.com/tiangolo/poetry-version-plugin
    poetry self add "poetry-dynamic-versioning[plugin]==v1.3.0" && \
    poetry self add "poetry-pyinstaller-plugin==1.1.10" && \
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
