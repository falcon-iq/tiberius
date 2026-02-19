import re

from bs4 import BeautifulSoup

from falcon_iq_analyzer.models.domain import PageInfo

REMOVE_TAGS = {"script", "style", "noscript", "svg", "iframe"}
BOILERPLATE_TAGS = {"nav", "footer", "header"}
COOKIE_CLASSES = {"cookie", "consent", "gdpr", "banner"}


def clean_page(page: PageInfo, raw_html: str, max_chars: int = 4000) -> PageInfo:
    """Extract clean text from raw HTML and populate page metadata."""
    soup = BeautifulSoup(raw_html, "lxml")

    # Extract metadata before stripping
    title_tag = soup.find("title")
    if title_tag:
        page.title = title_tag.get_text(strip=True)

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        page.meta_description = str(meta_desc["content"]).strip()

    # Remove unwanted tags
    for tag_name in REMOVE_TAGS:
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
