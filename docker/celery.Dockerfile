# Celery Worker & Beat Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r celery && useradd -r -g celery celery

# Create directory for persistent beat schedule
RUN mkdir -p /var/lib/celery/beat && chown -R celery:celery /var/lib/celery

# Copy all services to allow task discovery
COPY --chown=celery:celery services /app/services

# Install Common package from the local source
RUN pip install --no-cache-dir /app/services/common

# Install worker-specific tools
RUN pip install --no-cache-dir flower yfinance

# Ensure correct permissions for the app directory
RUN chown -R celery:celery /app

ENV PYTHONPATH=/app

USER celery

# Default command (overridden in docker-compose)
CMD ["celery", "-A", "common.celery_app", "worker", "--loglevel=INFO"]