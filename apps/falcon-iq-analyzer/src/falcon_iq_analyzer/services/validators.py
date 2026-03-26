"""Deterministic post-LLM validation rules.

Runs AFTER LLM extraction to drop invalid or nonsensical data.
No LLM calls — pure rule-based filtering.
"""

from __future__ import annotations

import logging

from falcon_iq_analyzer.models.domain import (
    ExtractedIntegration,
    Offering,
    PageExtraction,
    PricingPlan,
)

logger = logging.getLogger(__name__)

# Valid ISO 4217 currency codes (common subset)
_VALID_CURRENCIES = {
    "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR",
    "BRL", "MXN", "KRW", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF",
    "TRY", "ZAR", "SGD", "HKD", "NZD", "ILS", "AED", "SAR", "THB",
}

_VALID_BILLING_PERIODS = {"monthly", "annual", "one_time", "usage_based", "contact_sales"}


def validate_extractions(extractions: list[PageExtraction]) -> list[PageExtraction]:
    """Run all validation rules on a list of page extractions.

    Modifies extractions in-place: removes invalid items, fixes fixable issues.
    """
    for ext in extractions:
        ext.offerings = _validate_offerings(ext.offerings)
        ext.pricing_plans = _validate_pricing(ext.pricing_plans)
        ext.integrations = _validate_integrations(ext.integrations)

    return extractions


def _validate_offerings(offerings: list[Offering]) -> list[Offering]:
    """Validate and deduplicate offerings."""
    valid: list[Offering] = []
    seen_names: set[str] = set()

    for o in offerings:
        # Must have a product name
        if not o.product_name or not o.product_name.strip():
            logger.debug("Dropping offering with empty product name")
            continue

        # Dedup by normalized name
        name_key = o.product_name.strip().lower()
        if name_key in seen_names:
            logger.debug("Dropping duplicate offering: %s", o.product_name)
            continue
        seen_names.add(name_key)

        # Must have some substance (description or features)
        if not o.description and not o.features:
            logger.debug("Dropping offering '%s' — no description or features", o.product_name)
            continue

        # Trim absurdly long feature lists (likely hallucination)
        if len(o.features) > 20:
            o.features = o.features[:20]

        valid.append(o)

    return valid


def _validate_pricing(plans: list[PricingPlan]) -> list[PricingPlan]:
    """Validate pricing plans against deterministic rules."""
    valid: list[PricingPlan] = []
    seen_names: set[str] = set()

    for plan in plans:
        # Must have a name
        if not plan.name or not plan.name.strip():
            continue

        # Dedup
        name_key = plan.name.strip().lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        # Currency must be valid if provided
        if plan.currency and plan.currency.upper() not in _VALID_CURRENCIES:
            logger.debug("Fixing invalid currency '%s' for plan '%s'", plan.currency, plan.name)
            plan.currency = None

        # Price must be non-negative if provided
        if plan.price is not None and plan.price < 0:
            plan.price = None

        # Billing period must be valid
        if plan.billing_period not in _VALID_BILLING_PERIODS:
            plan.billing_period = "contact_sales"

        # "Contact sales" plans should not have a specific price
        if plan.billing_period == "contact_sales" and plan.price is not None:
            # If it says contact sales but has a price, trust the price
            plan.billing_period = "monthly"  # default assumption

        valid.append(plan)

    return valid


def _validate_integrations(integrations: list[ExtractedIntegration]) -> list[ExtractedIntegration]:
    """Validate integration entries."""
    valid: list[ExtractedIntegration] = []
    seen_names: set[str] = set()

    # Generic terms that are NOT integration names
    non_integration_names = {
        "integrations", "partners", "connect", "api", "popular tools",
        "leading platforms", "third-party", "ecosystem", "marketplace",
        "learn more", "see all", "view all", "home", "contact",
    }

    for integ in integrations:
        name = integ.name.strip()
        if not name:
            continue

        name_lower = name.lower()

        # Skip generic terms
        if name_lower in non_integration_names:
            continue

        # Skip very short or very long names
        if len(name) < 2 or len(name) > 80:
            continue

        # Dedup
        if name_lower in seen_names:
            continue
        seen_names.add(name_lower)

        # Validate integration type
        if integ.integration_type not in ("native", "api", "partner", "unknown"):
            integ.integration_type = "unknown"

        valid.append(integ)

    return valid
