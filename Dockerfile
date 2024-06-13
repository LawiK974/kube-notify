# Stage 1: Builder stage where the package is built using Poetry
FROM python:alpine3.20 as builder

WORKDIR /app
RUN apk update \
    # Install poetry dependencies
    && apk add gcc libc-dev libffi-dev git \
    # Fix CVE-2023-42364
    && apk upgrade busybox \
    # Clean cache
    && apk cache clean
RUN pip install poetry==1.8.3
COPY . /app
# Disable virtual env creation by poetry, it's not needed in Docker
RUN poetry config virtualenvs.create false
# Install poetry version plugin see https://github.com/tiangolo/poetry-version-plugin
RUN poetry self add "poetry-dynamic-versioning[plugin]==v1.3.0"
# Install dependencies only (to improve caching)
RUN poetry install --no-root --only main
# Build the package (this creates the package wheel)
RUN poetry build

# Stage 2: Lightweight production stage with minimal footprint
FROM python:alpine3.20 as production
WORKDIR /app
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl
ENV PYTHONUNBUFFERED=1
CMD ["kube-notify", "--config", "/app/config.yaml", "--inCluster"]
