# Multi-stage build for Falcon IQ Analyzer

# Stage 1: Install dependencies
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY --from=builder /app /app

# Create non-root user (AWS Fargate best practice)
RUN groupadd -r falcon && useradd -r -g falcon falcon
RUN mkdir -p /app/results && chown -R falcon:falcon /app

# Default to S3 storage in container (override for local dev)
ENV WEB_ANALYZER_STORAGE_TYPE=s3
ENV WEB_ANALYZER_HOST=0.0.0.0
ENV WEB_ANALYZER_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

USER falcon

ENTRYPOINT ["uv", "run", "uvicorn", "falcon_iq_analyzer.main:app", "--host", "0.0.0.0", "--port", "8000"]
