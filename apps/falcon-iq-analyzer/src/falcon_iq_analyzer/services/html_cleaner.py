import json
import logging
import re

from bs4 import BeautifulSoup

from falcon_iq_analyzer.models.domain import PageInfo, StructuredPageData

logger = logging.getLogger(__name__)

REMOVE_TAGS = {"style", "noscript", "svg", "iframe"}
BOILERPLATE_TAGS = {"nav", "footer", "header"}
COOKIE_CLASSES = {"cookie", "consent", "gdpr", "banner"}


def _extract_structured_data(soup: BeautifulSoup, page_url: str) -> StructuredPageData:
    """Extract structured data from HTML without any LLM involvement."""

    # 1. JSON-LD blocks
    json_ld: list[dict] = []
    for script_tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            raw = script_tag.string
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    json_ld.extend(parsed)
                else:
                    json_ld.append(parsed)
        except (json.JSONDecodeError, TypeError):
            pass

    # 2. Open Graph tags
    og_tags: dict[str, str] = {}
    for meta in soup.find_all("meta"):
        prop = meta.get("property", "") or meta.get("name", "")
        content = meta.get("content", "")
        if prop and content and (prop.startswith("og:") or prop.startswith("twitter:")):
            og_tags[prop] = content

    # 3. HTML tables (pricing grids, feature comparisons)
    tables: list[list[list[str]]] = []
    for table in soup.find_all("table"):
        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if rows and len(rows) >= 2:  # skip trivial 1-row tables
            tables.append(rows)

    # 4. Heading hierarchy (preserves page structure)
    headings: list[dict[str, str]] = []
    for level in ["h1", "h2", "h3"]:
        for h_tag in soup.find_all(level):
            text = h_tag.get_text(strip=True)
            if text and len(text) < 200:
                headings.append({"level": level, "text": text})

    # 5. Named links (integration/partner pages, customer logos)
    named_links: list[dict[str, str]] = []
    seen_texts: set[str] = set()
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True)
        href = a_tag["href"]
        if (
            text
            and len(text) < 100
            and text.lower() not in seen_texts
            and not text.startswith(("#", "javascript:"))
            and href
            and not href.startswith(("#", "javascript:"))
        ):
            named_links.append({"text": text, "href": href})
            seen_texts.add(text.lower())
        if len(named_links) >= 100:  # cap to avoid huge lists
            break

    return StructuredPageData(
        json_ld=json_ld,
        og_tags=og_tags,
        tables=tables,
        headings=headings,
        named_links=named_links,
    )


def clean_page(page: PageInfo, raw_html: str, max_chars: int = 4000) -> PageInfo:
    """Extract clean text and structured data from raw HTML."""
    soup = BeautifulSoup(raw_html, "lxml")

    # Extract metadata before stripping
    title_tag = soup.find("title")
    if title_tag:
        page.title = title_tag.get_text(strip=True)

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        page.meta_description = str(meta_desc["content"]).strip()

    # Extract structured data BEFORE removing scripts (need JSON-LD)
    page.structured_data = _extract_structured_data(soup, page.url_path)

    # Remove unwanted tags (including scripts now that we've extracted JSON-LD)
    for tag_name in REMOVE_TAGS | {"script"}:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove boilerplate sections
    for tag_name in BOILERPLATE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove cookie banners by class/id
    to_remove = []
    for element in soup.find_all(True):
        if element.attrs is None:
            continue
        classes = " ".join(element.get("class", []))
        el_id = element.get("id", "")
        combined = f"{classes} {el_id}".lower()
        if any(kw in combined for kw in COOKIE_CLASSES):
            to_remove.append(element)
    for element in to_remove:
        element.decompose()

    # Extract text
    text = soup.get_text(separator="\n", strip=True)

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    page.clean_text = text[:max_chars]
    return page
