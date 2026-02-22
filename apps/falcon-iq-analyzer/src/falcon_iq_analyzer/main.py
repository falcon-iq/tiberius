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


# Serve the React web app build output (only when dist has been built)
_repo_root = Path(__file__).parents[4]
_static_dir = _repo_root / "apps" / "falcon-iq-analyzer-web-app" / "dist"

if _static_dir.exists():
    # SPA catch-all: must be registered BEFORE the StaticFiles mount so that
    # unknown paths (e.g. /benchmark on hard refresh) return the SPA shell.
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        return FileResponse(str(_static_dir / "index.html"))

    # Mount static files last so API routes take priority
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "falcon_iq_analyzer.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
