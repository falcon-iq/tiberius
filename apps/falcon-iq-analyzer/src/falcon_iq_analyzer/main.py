import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.routers import analyze, benchmark, compare, crawl, report
from falcon_iq_analyzer.storage import create_storage_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Falcon IQ Analyzer",
    description="Analyze crawled web pages using LLMs to extract product offerings and generate selling scripts",
    version="0.1.0",
)

app.include_router(analyze.router, tags=["analyze"])
app.include_router(compare.router, tags=["compare"])
app.include_router(report.router, tags=["report"])
app.include_router(crawl.router, tags=["crawl"])
app.include_router(benchmark.router, tags=["benchmark"])


@app.get("/health")
async def health() -> dict:
    storage = create_storage_service()
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "storage_type": settings.storage_type,
        "storage_healthy": storage.is_healthy(),
    }


# Serve the React web app build output (only when dist has been built).
# Walk up to the repo root (varies between local dev and Docker).
_this = Path(__file__).resolve()
_repo_root = next((p for p in _this.parents if (p / "nx.json").exists()), None)
_static_dir = (_repo_root / "apps" / "falcon-iq-analyzer-web-app" / "dist") if _repo_root else None

# Known API path prefixes — the SPA fallback must never intercept these.
_API_PREFIXES = (
    "health", "analyze", "compare", "report", "crawl",
    "benchmark", "sites", "analyses", "benchmarks",
)

if _static_dir is not None and _static_dir.exists():
    # Serve JS/CSS/images at /static so the mount never shadows API routes.
    app.mount(
        "/static",
        StaticFiles(directory=str(_static_dir), html=False),
        name="static",
    )

    # SPA catch-all: only for GET requests on non-API paths (e.g. /benchmark
    # on hard refresh). API routes registered above take priority over this.
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        # If the path matches a real static file, serve it directly
        candidate = _static_dir / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_static_dir / "index.html"))


if __name__ == "__main__":
    uvicorn.run(
        "falcon_iq_analyzer.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
