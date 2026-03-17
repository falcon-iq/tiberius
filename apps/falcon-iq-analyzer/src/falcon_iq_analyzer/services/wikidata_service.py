"""Fetch verified company facts from Wikidata."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary"
USER_AGENT = "FalconIQ-Analyzer/1.0 (https://trymarketpilot.com)"

# Wikidata property IDs for company facts
PROPS = {
    "P571": "Founded",
    "P1128": "Employees",
    "P2139": "Revenue",
    "P159": "Headquarters",
    "P169": "CEO",
    "P452": "Industry",
    "P946": "ISIN",
}

PROP_IDS = "|".join(PROPS.keys())


async def search_wikidata_entity(company_name: str) -> str | None:
    """Search Wikidata for a company and return the entity ID (e.g. Q44294)."""
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": USER_AGENT}) as client:
        resp = await client.get(WIKIDATA_API, params={
            "action": "wbsearchentities",
            "search": company_name,
            "language": "en",
            "type": "item",
            "limit": "5",
            "format": "json",
        })
        resp.raise_for_status()
        data = resp.json()

        results = data.get("search", [])
        if not results:
            return None

        # Prefer results that mention "company", "corporation", "manufacturer" in description
        company_keywords = {"company", "corporation", "manufacturer", "automaker", "conglomerate", "inc", "ltd"}
        for result in results:
            desc = (result.get("description") or "").lower()
            if any(kw in desc for kw in company_keywords):
                return result["id"]

        # Fall back to first result
        return results[0]["id"]


async def get_entity_claims(entity_id: str) -> dict[str, Any]:
    """Fetch claims (facts) for a Wikidata entity via wbgetentities."""
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": USER_AGENT}) as client:
        resp = await client.get(WIKIDATA_API, params={
            "action": "wbgetentities",
            "ids": entity_id,
            "props": "claims",
            "format": "json",
        })
        resp.raise_for_status()
        entities = resp.json().get("entities", {})
        entity = entities.get(entity_id, {})
        return entity.get("claims", {})


async def resolve_entity_label(entity_id: str) -> str:
    """Resolve a Wikidata entity ID to its English label."""
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": USER_AGENT}) as client:
        resp = await client.get(WIKIDATA_API, params={
            "action": "wbgetentities",
            "ids": entity_id,
            "props": "labels",
            "languages": "en",
            "format": "json",
        })
        resp.raise_for_status()
        entities = resp.json().get("entities", {})
        entity = entities.get(entity_id, {})
        labels = entity.get("labels", {})
        en_label = labels.get("en", {})
        return en_label.get("value", entity_id)


def _extract_time_value(claim: dict) -> str | None:
    """Extract a date from a Wikidata time claim."""
    try:
        snak = claim["mainsnak"]["datavalue"]["value"]
        time_str = snak.get("time", "")
        # Format: +1903-06-16T00:00:00Z → 1903
        if time_str.startswith("+"):
            time_str = time_str[1:]
        year = time_str.split("-")[0]
        return year
    except (KeyError, IndexError):
        return None


def _extract_quantity_value(claim: dict) -> tuple[str | None, str | None]:
    """Extract a quantity and unit from a Wikidata quantity claim."""
    try:
        snak = claim["mainsnak"]["datavalue"]["value"]
        amount = snak.get("amount", "")
        unit = snak.get("unit", "")

        # Clean amount: "+1234567" → "1,234,567"
        if amount.startswith("+"):
            amount = amount[1:]

        try:
            num = float(amount)
            if num >= 1_000_000_000:
                amount_str = f"~{num / 1_000_000_000:.1f}B"
            elif num >= 1_000_000:
                amount_str = f"~{num / 1_000_000:.0f}M"
            elif num >= 1_000:
                amount_str = f"~{num / 1_000:.0f}K"
            else:
                amount_str = f"{int(num):,}"
        except ValueError:
            amount_str = amount

        # Extract currency from unit URL
        unit_label = ""
        if "Q4917" in unit:  # US Dollar
            unit_label = "USD"
        elif "Q4916" in unit:  # Euro
            unit_label = "EUR"
        elif "Q25224" in unit:  # GBP
            unit_label = "GBP"
        elif "Q1104394" in unit:  # JPY
            unit_label = "JPY"

        return amount_str, unit_label
    except (KeyError, IndexError):
        return None, None


def _extract_entity_id(claim: dict) -> str | None:
    """Extract an entity ID from a Wikidata entity claim."""
    try:
        snak = claim["mainsnak"]["datavalue"]["value"]
        return snak.get("id")
    except (KeyError, IndexError):
        return None


def _get_point_in_time(claim: dict) -> str:
    """Extract the point-in-time qualifier from a claim if present."""
    qualifiers = claim.get("qualifiers", {})
    pit = qualifiers.get("P585", [])  # P585 = point in time
    if pit:
        try:
            time_str = pit[0]["datavalue"]["value"]["time"]
            if time_str.startswith("+"):
                time_str = time_str[1:]
            return time_str.split("-")[0]
        except (KeyError, IndexError):
            pass
    return ""


async def fetch_company_facts(company_name: str, company_url: str) -> list[dict]:
    """Fetch verified facts about a company from Wikidata.

    Returns a list of dicts with keys: label, value, source, source_url.
    """
    facts: list[dict] = []

    try:
        entity_id = await search_wikidata_entity(company_name)
        if not entity_id:
            logger.info("No Wikidata entity found for %s", company_name)
            return facts

        claims = await get_entity_claims(entity_id)
        wikidata_url = f"https://www.wikidata.org/wiki/{entity_id}"
        wikipedia_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"

        # Founded (P571) — pick the earliest
        if "P571" in claims:
            for claim in claims["P571"]:
                year = _extract_time_value(claim)
                if year:
                    facts.append({
                        "label": "Founded",
                        "value": year,
                        "source": "Wikidata",
                        "sourceUrl": wikidata_url,
                    })
                    break

        # Headquarters (P159) — pick preferred or first
        if "P159" in claims:
            for claim in claims["P159"]:
                rank = claim.get("rank", "normal")
                hq_id = _extract_entity_id(claim)
                if hq_id:
                    try:
                        hq_label = await resolve_entity_label(hq_id)
                        facts.append({
                            "label": "Headquarters",
                            "value": hq_label,
                            "source": "Wikidata",
                            "sourceUrl": wikidata_url,
                        })
                        break
                    except Exception:
                        pass

        # Employees (P1128) — pick the most recent (preferred rank first)
        if "P1128" in claims:
            best_claim = None
            best_year = ""
            for claim in claims["P1128"]:
                pit = _get_point_in_time(claim)
                rank = claim.get("rank", "normal")
                if rank == "preferred" or (not best_claim) or (pit > best_year):
                    best_claim = claim
                    best_year = pit
                    if rank == "preferred":
                        break

            if best_claim:
                amount, _ = _extract_quantity_value(best_claim)
                if amount:
                    year_note = f" ({best_year})" if best_year else ""
                    facts.append({
                        "label": "Employees",
                        "value": f"{amount}{year_note}",
                        "source": "Wikidata",
                        "sourceUrl": wikidata_url,
                    })

        # Revenue (P2139) — pick the most recent
        if "P2139" in claims:
            best_claim = None
            best_year = ""
            for claim in claims["P2139"]:
                pit = _get_point_in_time(claim)
                rank = claim.get("rank", "normal")
                if rank == "preferred" or (not best_claim) or (pit > best_year):
                    best_claim = claim
                    best_year = pit
                    if rank == "preferred":
                        break

            if best_claim:
                amount, currency = _extract_quantity_value(best_claim)
                if amount:
                    year_note = f" ({best_year})" if best_year else ""
                    currency_prefix = f"{currency} " if currency else ""
                    facts.append({
                        "label": "Revenue",
                        "value": f"{currency_prefix}{amount}{year_note}",
                        "source": "Wikidata",
                        "sourceUrl": wikidata_url,
                    })

        # CEO (P169) — pick preferred or first
        if "P169" in claims:
            for claim in claims["P169"]:
                rank = claim.get("rank", "normal")
                ceo_id = _extract_entity_id(claim)
                if ceo_id:
                    try:
                        ceo_label = await resolve_entity_label(ceo_id)
                        facts.append({
                            "label": "CEO",
                            "value": ceo_label,
                            "source": "Wikidata",
                            "sourceUrl": wikidata_url,
                        })
                        break
                    except Exception:
                        pass

        # Add Wikipedia link as a general reference
        facts.append({
            "label": "Wikipedia",
            "value": company_name,
            "source": "Wikipedia",
            "sourceUrl": wikipedia_url,
        })

        logger.info("Fetched %d facts from Wikidata for %s (%s)", len(facts), company_name, entity_id)

    except Exception:
        logger.exception("Failed to fetch Wikidata facts for %s", company_name)

    return facts
