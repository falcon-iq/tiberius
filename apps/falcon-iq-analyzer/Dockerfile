# Multi-stage build for Falcon IQ Analyzer

# Stage 1: Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY pyproject.toml .
COPY src/ ./src/

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

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

ENTRYPOINT ["python", "-m", "uvicorn", "falcon_iq_analyzer.main:app", "--host", "0.0.0.0", "--port", "8000"]
