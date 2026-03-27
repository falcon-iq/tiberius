"""External enrichment services — HTTP client to crawler + LLM claim verification."""

from falcon_iq_analyzer.services.enrichment.client import (
    fetch_all_enrichments,
    fetch_enrichment,
)
from falcon_iq_analyzer.services.enrichment.verifier import verify_claims

__all__ = ["fetch_enrichment", "fetch_all_enrichments", "verify_claims"]
