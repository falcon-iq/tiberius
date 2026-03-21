# Multi-stage build for Falcon IQ Analyzer
# Build context: repo root (set by build.sh -f flag)

# Stage 1: Install dependencies
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Mirror repo layout so the relative path in [tool.uv.sources] resolves
WORKDIR /repo/apps/falcon-iq-analyzer

# Copy notification library (local dependency at ../../libs/notifications/python)
COPY libs/notifications/python/ /repo/libs/notifications/python/

# Copy analyzer source and install
COPY apps/falcon-iq-analyzer/pyproject.toml apps/falcon-iq-analyzer/uv.lock ./
COPY apps/falcon-iq-analyzer/src/ ./src/
RUN uv sync --frozen --no-dev

# Stage 2: Runtime — mirror same layout so uv.sources path resolves at runtime
FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Keep same directory structure as build stage
WORKDIR /repo/apps/falcon-iq-analyzer
COPY --from=builder /repo/apps/falcon-iq-analyzer /repo/apps/falcon-iq-analyzer
COPY --from=builder /repo/libs/notifications/python /repo/libs/notifications/python

# Copy notification templates
COPY libs/notifications/templates/ /repo/libs/notifications/templates/

# Create non-root user (AWS Fargate best practice)
RUN groupadd -r falcon && useradd -r -g falcon -m falcon
RUN mkdir -p /repo/apps/falcon-iq-analyzer/results && chown -R falcon:falcon /repo

# Default to S3 storage in container (override for local dev)
ENV WEB_ANALYZER_STORAGE_TYPE=s3
ENV WEB_ANALYZER_HOST=0.0.0.0
ENV WEB_ANALYZER_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

USER falcon

ENTRYPOINT ["uv", "run", "uvicorn", "falcon_iq_analyzer.main:app", "--host", "0.0.0.0", "--port", "8000"]
