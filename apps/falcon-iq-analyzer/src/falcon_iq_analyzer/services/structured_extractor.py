"""Deterministic structured data extraction from HTML — no LLM involved.

Extracts pricing plans, integrations, and product info from JSON-LD,
HTML tables, and page structure before the LLM ever touches the data.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from falcon_iq_analyzer.models.domain import (
    Evidence,
    ExtractedIntegration,
    PageInfo,
    PricingPlan,
    StructuredPageData,
)

logger = logging.getLogger(__name__)

# URL patterns that indicate integration/partner pages
_INTEGRATION_URL_PATTERNS = re.compile(
    r"/(integrations?|partners?|connect|apps|marketplace|ecosystem)",
    re.IGNORECASE,
)

# URL patterns for pricing pages
_PRICING_URL_PATTERNS = re.compile(
    r"/(pricing|plans?|packages|billing)",
    re.IGNORECASE,
)

# Common billing period keywords
_BILLING_KEYWORDS = {
    "month": "monthly",
    "mo": "monthly",
    "/mo": "monthly",
    "monthly": "monthly",
    "year": "annual",
    "yr": "annual",
    "/yr": "annual",
    "annual": "annual",
    "annually": "annual",
    "one-time": "one_time",
    "one time": "one_time",
    "per user": "monthly",
    "contact": "contact_sales",
    "custom": "contact_sales",
    "enterprise": "contact_sales",
    "get a quote": "contact_sales",
}


def extract_structured_data(page: PageInfo) -> dict[str, Any]:
    """Extract deterministic facts from a page's structured data.

    Returns a dict with keys: pricing_plans, integrations, json_ld_products.
    This is passed into the LLM extraction prompt as pre-verified facts.
    """
    sd = page.structured_data
    if not sd:
        return {"pricing_plans": [], "integrations": [], "json_ld_products": []}

    pricing_plans = _extract_pricing_from_tables(sd, page.url_path)
    integrations = _extract_integrations(sd, page)
    json_ld_products = _extract_json_ld_products(sd, page.url_path)

    return {
        "pricing_plans": pricing_plans,
        "integrations": integrations,
        "json_ld_products": json_ld_products,
    }


def _extract_pricing_from_tables(
    sd: StructuredPageData,
    url_path: str,
) -> list[PricingPlan]:
    """Extract pricing plans from HTML tables on pricing pages."""
    plans: list[PricingPlan] = []

    for table in sd.tables:
        if len(table) < 2:
            continue

        # Look for tables with price-like values
        for row in table:
            for cell in row:
                # Check if cell contains a price pattern ($XX, €XX, etc.)
                price_match = re.search(r"[\$€£¥][\d,]+(?:\.\d{2})?", cell)
                if price_match:
                    price_str = price_match.group()
                    # Extract currency and amount
                    currency_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                    currency = currency_map.get(price_str[0], "USD")
                    try:
                        price = float(price_str[1:].replace(",", ""))
                    except ValueError:
                        continue

                    # Try to find plan name (usually first cell or a heading)
                    plan_name = row[0] if row[0] != cell else "Plan"

                    # Detect billing period from surrounding text
                    full_row_text = " ".join(row).lower()
                    billing_period = "monthly"  # default
                    for keyword, period in _BILLING_KEYWORDS.items():
                        if keyword in full_row_text:
                            billing_period = period
                            break

                    plans.append(
                        PricingPlan(
                            name=plan_name,
                            price=price,
                            currency=currency,
                            billing_period=billing_period,
                            evidence=[Evidence(url=url_path, quote=f"Table row: {' | '.join(row)}"[:280])],
                            confidence=0.9,  # deterministic extraction = high confidence
                        )
                    )
                    break  # one plan per row

    return plans


def _extract_integrations(
    sd: StructuredPageData,
    page: PageInfo,
) -> list[ExtractedIntegration]:
    """Extract integration names from integration/partner pages."""
    integrations: list[ExtractedIntegration] = []

    # Only extract from pages whose URL looks like an integrations page
    if not _INTEGRATION_URL_PATTERNS.search(page.url_path):
        return integrations

    seen: set[str] = set()

    # From named links (integration pages often list partners as links)
    for link in sd.named_links:
        name = link["text"].strip()
        href = link.get("href", "")

        # Skip navigation/generic links
        if len(name) < 2 or len(name) > 60:
            continue
        if name.lower() in {"home", "about", "contact", "login", "sign up", "pricing", "blog"}:
            continue

        name_lower = name.lower()
        if name_lower not in seen:
            seen.add(name_lower)
            integrations.append(
                ExtractedIntegration(
                    name=name,
                    integration_type="native" if "/integrations" in href.lower() else "unknown",
                    evidence=[Evidence(url=page.url_path, quote=f'Link: "{name}" ({href})'[:280])],
                    confidence=0.85,
                )
            )

    # From headings (some integration pages use H2/H3 per partner)
    for heading in sd.headings:
        if heading["level"] in ("h2", "h3"):
            name = heading["text"].strip()
            name_lower = name.lower()
            if (
                name_lower not in seen
                and len(name) > 2
                and len(name) < 60
                and not any(kw in name_lower for kw in ["integration", "partner", "connect", "our", "all", "more"])
            ):
                seen.add(name_lower)
                integrations.append(
                    ExtractedIntegration(
                        name=name,
                        integration_type="unknown",
                        evidence=[Evidence(url=page.url_path, quote=f"Heading: {name}"[:280])],
                        confidence=0.7,
                    )
                )

    return integrations


def _extract_json_ld_products(
    sd: StructuredPageData,
    url_path: str,
) -> list[dict[str, Any]]:
    """Extract product/offer data from JSON-LD structured data."""
    products: list[dict[str, Any]] = []

    for block in sd.json_ld:
        ld_type = block.get("@type", "")

        # Handle both single type and list of types
        types = ld_type if isinstance(ld_type, list) else [ld_type]

        if any(t in ("Product", "SoftwareApplication", "WebApplication", "Service") for t in types):
            product: dict[str, Any] = {
                "name": block.get("name", ""),
                "description": block.get("description", ""),
                "source_url": url_path,
            }

            # Extract offers/pricing from JSON-LD
            offers = block.get("offers", {})
            if isinstance(offers, dict):
                product["price"] = offers.get("price")
                product["currency"] = offers.get("priceCurrency")
            elif isinstance(offers, list) and offers:
                product["price"] = offers[0].get("price")
                product["currency"] = offers[0].get("priceCurrency")

            # Extract aggregate rating
            rating = block.get("aggregateRating", {})
            if rating:
                product["rating"] = rating.get("ratingValue")
                product["review_count"] = rating.get("reviewCount")

            if product.get("name"):
                products.append(product)

        elif any(t in ("Organization", "Corporation", "LocalBusiness") for t in types):
            # Organization-level data (company info)
            products.append(
                {
                    "type": "organization",
                    "name": block.get("name", ""),
                    "description": block.get("description", ""),
                    "source_url": url_path,
                    "founding_date": block.get("foundingDate"),
                    "employee_count": block.get("numberOfEmployees"),
                }
            )

    return products
