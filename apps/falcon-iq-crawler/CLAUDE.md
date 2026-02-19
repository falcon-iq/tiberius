# Falcon IQ Crawler

## Overview

Web crawler microservice that crawls websites via API and stores results in local filesystem or S3.

## Tech Stack

- Java 21 + Embedded Jetty 12 + Jersey 3
- JSoup for HTML parsing
- AWS SDK v2 for S3 storage
- Maven (fat JAR via shade plugin)

## Commands

```bash
nx run falcon-iq-crawler:build     # Build fat JAR
nx run falcon-iq-crawler:test      # Run tests
nx run falcon-iq-crawler:serve     # Start server (port 8080)
nx run falcon-iq-crawler:clean     # Clean build artifacts
```

## API Endpoints

- `POST /api/crawl` - Start a crawl (returns 202 with crawlId)
- `GET /api/crawl/{id}/status` - Check crawl progress
- `GET /api/health` - Health check

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `STORAGE_TYPE` | `local` | `local` or `s3` |
| `OUTPUT_DIR` | `crawled_pages` | Output dir (local mode) |
| `S3_BUCKET_NAME` | — | S3 bucket (required for s3 mode) |
| `AWS_REGION` | `us-east-1` | AWS region (s3 mode) |
| `PORT` | `8080` | Server port |
| `MAX_CONCURRENT_CRAWLS` | `3` | Max concurrent crawl jobs |

## Architecture

- `api/` - REST endpoints (CrawlResource, HealthCheckResource)
- `core/` - Crawler logic (WebCrawler, PageFetcher, LinkExtractor, CrawlManager)
- `storage/` - Storage abstraction (StorageService, LocalStorageService, S3StorageService)

## Docker

```bash
docker-compose up --build      # Run locally on port 8081
./build.sh v1.0.0 push         # Build and push to ECR
```
