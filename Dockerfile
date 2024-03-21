# Stage 1: Builder stage where the package is built using Poetry
FROM python:3.12-slim as builder

WORKDIR /app
RUN pip install poetry
COPY . /app
# Disable virtual env creation by poetry, it's not needed in Docker
RUN poetry config virtualenvs.create false
# Install dependencies only (to improve caching)
RUN poetry install --no-root --no-dev
# Build the package (this creates the package wheel)
RUN poetry build

# Stage 2: Lightweight production stage with minimal footprint
FROM python:3.12-slim as production
WORKDIR /app
COPY --from=builder /app/dist/*.whl /app/
RUN pip install --no-cache-dir /app/*.whl
CMD ["kube-notify", "--config", "/app/config.yaml", "--inCluster"]
