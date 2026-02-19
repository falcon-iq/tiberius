# Falcon IQ Analyzer

LLM-powered web page analysis service that crawls websites, classifies pages, extracts product offerings, generates selling scripts, and benchmarks competitive positioning.

## Prerequisites

- Python 3.11+ (via Homebrew: `brew install python@3.11`)
- Java 21 (for the crawler service)
- Maven (for building the crawler)
- An OpenAI API key (or local Ollama instance)

## Quick Start

### 1. Build and start the crawler (Terminal 1)

```bash
cd apps/falcon-iq-crawler
mvn package -DskipTests
java -jar target/falcon-iq-crawler-1.0.0.jar
```

The crawler starts on **port 8080**.

### 2. Set up and start the analyzer (Terminal 2)

```bash
cd apps/falcon-iq-analyzer

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set your OpenAI API key
export WEB_ANALYZER_OPENAI_API_KEY="sk-your-key-here"

# Start the analyzer
python -m uvicorn falcon_iq_analyzer.main:app --host 0.0.0.0 --port 8000 --reload
```

The analyzer starts on **port 8000**.

### 3. Run the full pipeline (Terminal 3)

**Step 1: Health check**

```bash
curl http://localhost:8000/health
```

**Step 2: Start a crawl**

```bash
curl -X POST http://localhost:8000/crawl -H 'Content-Type: application/json' -d '{"url":"https://example.com","max_pages":100}'
```

Response includes a `job_id`. Poll until status is `completed`:

```bash
curl http://localhost:8000/crawl/<job_id>
```

**Step 3: Find the crawl directory**

The crawler saves pages to `apps/falcon-iq-crawler/crawled_pages/<crawl_uuid>/`. List crawl directories:

```bash
ls apps/falcon-iq-crawler/crawled_pages/
```

**Step 4: Start analysis**

```bash
curl -X POST http://localhost:8000/analyze -H 'Content-Type: application/json' -d '{"crawl_directory":"/full/path/to/apps/falcon-iq-crawler/crawled_pages/<crawl_uuid>","company_name":"Company Name"}'
```

Poll until completed:

```bash
curl http://localhost:8000/analyze/<job_id>
```

**Step 5: Download the report**

```bash
curl http://localhost:8000/report/<job_id>
```

### 4. Compare two companies

After analyzing two companies, compare them:

```bash
curl -X POST http://localhost:8000/compare -H 'Content-Type: application/json' -d '{"job_id_a":"<analysis_job_id_1>","job_id_b":"<analysis_job_id_2>"}'
```

### 5. Run a competitive benchmark

```bash
curl -X POST http://localhost:8000/benchmark -H 'Content-Type: application/json' -d '{"job_id_a":"<analysis_job_id_1>","job_id_b":"<analysis_job_id_2>","num_prompts":15}'
```

Poll until completed:

```bash
curl http://localhost:8000/benchmark/<job_id>
```

## Docker (Alternative)

Run both services together without manual setup:

```bash
cd apps/falcon-iq-analyzer
export WEB_ANALYZER_OPENAI_API_KEY="sk-your-key-here"
docker-compose up --build
```

This starts:
- Crawler on port **8081**
- Analyzer on port **8000**

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/crawl` | Start a crawl (`{"url":"...","max_pages":100}`) |
| GET | `/crawl/{job_id}` | Check crawl status |
| GET | `/sites` | List crawled sites |
| POST | `/analyze` | Start analysis (`{"crawl_directory":"...","company_name":"..."}`) |
| GET | `/analyze/{job_id}` | Check analysis status |
| GET | `/analyses` | List completed analyses |
| POST | `/compare` | Compare two analyses (`{"job_id_a":"...","job_id_b":"..."}`) |
| GET | `/report/{job_id}` | Download markdown report |
| POST | `/benchmark` | Start benchmark (`{"job_id_a":"...","job_id_b":"...","num_prompts":15}`) |
| GET | `/benchmark/{job_id}` | Check benchmark status |
| GET | `/benchmarks` | List completed benchmarks |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_ANALYZER_OPENAI_API_KEY` | — | **Required** for OpenAI mode |
| `WEB_ANALYZER_LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `WEB_ANALYZER_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `WEB_ANALYZER_CRAWLER_API_URL` | `http://localhost:8080` | Crawler service URL |
| `WEB_ANALYZER_STORAGE_TYPE` | `local` | `local` or `s3` |
| `WEB_ANALYZER_S3_BUCKET_NAME` | — | Required for S3 mode |
| `WEB_ANALYZER_AWS_REGION` | `us-east-1` | AWS region |
| `WEB_ANALYZER_HOST` | `0.0.0.0` | Server bind host |
| `WEB_ANALYZER_PORT` | `8000` | Server port |

For Ollama (local LLM, no API key needed):

```bash
export WEB_ANALYZER_LLM_PROVIDER=ollama
export WEB_ANALYZER_OLLAMA_BASE_URL=http://localhost:11434
export WEB_ANALYZER_OLLAMA_MODEL=mistral
```

## Running Tests

```bash
cd apps/falcon-iq-analyzer
source .venv/bin/activate
python -m pytest tests/ -v
```

## Linting

```bash
ruff check src/
ruff format --check src/
```

## Pipeline Overview

The analysis pipeline runs 6 steps:

1. **Load pages** — Find all HTML files in the crawl directory
2. **Clean HTML** — Strip boilerplate, extract text content
3. **Classify pages** — LLM categorizes each page (product, blog, legal, etc.)
4. **Extract offerings** — LLM extracts product info from product/industry pages
5. **Synthesize** — LLM identifies top 5 offerings with selling scripts
6. **Generate report** — Produces a markdown report

Results are cached per-page, so re-running analysis on the same crawl skips already-processed pages.
