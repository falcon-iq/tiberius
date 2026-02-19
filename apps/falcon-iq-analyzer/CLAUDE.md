# Falcon IQ Analyzer

## Overview

LLM-powered web page analysis microservice. Analyzes crawled websites to classify pages, extract product offerings, synthesize selling scripts, and benchmark competitive positioning.

## Tech Stack

- Python 3.11 + FastAPI + Uvicorn
- OpenAI / Ollama for LLM inference
- httpx for async HTTP (crawler API integration)
- BeautifulSoup4 + lxml for HTML parsing
- boto3 for S3 storage
- Pydantic for data validation

## Commands

```bash
nx run falcon-iq-analyzer:serve    # Start dev server (port 8000)
nx run falcon-iq-analyzer:test     # Run tests
nx run falcon-iq-analyzer:lint     # Lint with ruff
nx run falcon-iq-analyzer:format   # Check formatting with ruff
nx run falcon-iq-analyzer:build    # Install package in editable mode
```

## API Endpoints

- `POST /crawl` - Start a crawl via falcon-iq-crawler HTTP API
- `GET /crawl/{job_id}` - Check crawl status
- `GET /sites` - List crawled sites
- `POST /analyze` - Start analysis pipeline
- `GET /analyze/{job_id}` - Check analysis status
- `GET /analyses` - List completed analyses
- `POST /compare` - Compare two analyses
- `GET /report/{job_id}` - Download markdown report
- `POST /benchmark` - Start competitive benchmark
- `GET /benchmark/{job_id}` - Check benchmark status
- `GET /benchmarks` - List completed benchmarks
- `GET /health` - Health check

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `WEB_ANALYZER_LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `WEB_ANALYZER_OPENAI_API_KEY` | — | Required for OpenAI mode |
| `WEB_ANALYZER_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |
| `WEB_ANALYZER_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama URL |
| `WEB_ANALYZER_OLLAMA_MODEL` | `mistral` | Ollama model |
| `WEB_ANALYZER_CRAWLER_API_URL` | `http://localhost:8080` | Crawler service URL |
| `WEB_ANALYZER_STORAGE_TYPE` | `local` | `local` or `s3` |
| `WEB_ANALYZER_S3_BUCKET_NAME` | — | Required for S3 mode |
| `WEB_ANALYZER_AWS_REGION` | `us-east-1` | AWS region |
| `WEB_ANALYZER_RESULTS_DIR` | `results` | Local results directory |
| `WEB_ANALYZER_CRAWLED_SITES_DIR` | `crawled_sites` | Local crawled pages dir |
| `WEB_ANALYZER_HOST` | `0.0.0.0` | Server host |
| `WEB_ANALYZER_PORT` | `8000` | Server port |

## Architecture

- `models/` - Pydantic domain models, request/response schemas
- `llm/` - LLM client abstraction (OpenAI, Ollama)
- `services/` - Business logic (crawler client, classifier, extractor, synthesizer, etc.)
- `storage/` - Storage abstraction (local filesystem, S3)
- `cache/` - Disk-based analysis cache
- `pipeline/` - Orchestration (analyzer, benchmark, job manager)
- `routers/` - FastAPI route handlers

## Docker

```bash
docker-compose up --build      # Run analyzer + crawler locally
./build.sh v1.0.0 push         # Build and push to ECR
```
