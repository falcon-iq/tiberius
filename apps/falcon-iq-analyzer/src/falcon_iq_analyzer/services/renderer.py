"""Playwright-based headless rendering service for JS-heavy pages."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

# Module-level browser instance (lazy-initialized)
_browser = None
_playwright = None

MAX_PAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
RENDER_TIMEOUT_MS = 30_000
NAVIGATION_TIMEOUT_MS = 20_000


class RenderRequest(BaseModel):
    url: HttpUrl
    timeout_ms: int = RENDER_TIMEOUT_MS
    wait_until: str = "networkidle"  # "load", "domcontentloaded", "networkidle"


class RenderResponse(BaseModel):
    url: str
    html: str
    final_url: str
    title: str
    rendered: bool


async def _get_browser():
    """Lazy-initialize a shared Playwright browser instance."""
    global _browser, _playwright
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright

        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        logger.info("Playwright browser launched")
    return _browser


async def shutdown_browser():
    """Close the browser and Playwright — call on app shutdown."""
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
    logger.info("Playwright browser shut down")


async def render_page(url: str, timeout_ms: int = RENDER_TIMEOUT_MS, wait_until: str = "networkidle") -> RenderResponse:
    """Render a single page with headless Chromium and return the full HTML."""
    browser = await _get_browser()
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 720},
        java_script_enabled=True,
        locale="en-US",
    )
    page = await context.new_page()

    # Hide webdriver/automation markers
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """)

    try:
        response = await page.goto(str(url), wait_until=wait_until, timeout=timeout_ms)

        if response and response.status >= 400:
            raise HTTPException(status_code=502, detail=f"Upstream returned {response.status}")

        # Wait a bit for any late JS to settle
        await page.wait_for_timeout(1000)

        html = await page.content()

        if len(html.encode("utf-8")) > MAX_PAGE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Rendered page exceeds 5 MB limit")

        title = await page.title()
        final_url = page.url

        return RenderResponse(
            url=str(url),
            html=html,
            final_url=final_url,
            title=title,
            rendered=True,
        )
    finally:
        await context.close()


# --- FastAPI Router ---

router = APIRouter(tags=["renderer"])


@router.post("/render", response_model=RenderResponse)
async def render_endpoint(req: RenderRequest):
    """Render a JS-heavy page using headless Chromium and return the full HTML."""
    try:
        return await render_page(str(req.url), req.timeout_ms, req.wait_until)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Render failed for %s", req.url)
        raise HTTPException(status_code=500, detail=str(e))
