"""Additional tests for enrichment: HTML report, verifier, client, pipeline error handling."""

from __future__ import annotations

import json

import pytest

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.models.company_benchmark import (
    CompanyOfferingSummary,
    CompanyOverview,
    MultiCompanyBenchmarkResult,
    MultiCompanyBenchmarkSummary,
    MultiCompanyPromptEvaluation,
    MultiCompanyStats,
    ProductComparisonGroup,
)
from falcon_iq_analyzer.models.domain import AnalysisResult, CompanyMention, GeneratedPrompt
from falcon_iq_analyzer.models.enrichment import (
    CrunchbaseData,
    EnrichedCompanyProfile,
    EnrichmentResult,
    ExternalSource,
    G2Data,
    GoogleSearchInsight,
    ReviewSiteData,
    ReviewTheme,
    VerifiedClaim,
)
from falcon_iq_analyzer.services.enrichment.client import _snake_keys, fetch_enrichment
from falcon_iq_analyzer.services.enrichment.verifier import (
    _parse_verification_response,
    verify_claims,
)
from falcon_iq_analyzer.services.html_report_generator import (
    _render_external_validation,
    _render_fact_check_section,
    generate_html_report,
)


# ── Shared fixtures ──────────────────────────────────────────────────────


def _make_enrichment(name: str) -> EnrichmentResult:
    return EnrichmentResult(
        company_name=name,
        g2=G2Data(
            rating=4.5,
            review_count=1000,
            pros_themes=[ReviewTheme(theme="Easy to use", sentiment="positive")],
            cons_themes=[ReviewTheme(theme="Expensive", sentiment="negative")],
        ),
        crunchbase=CrunchbaseData(
            founded="2015",
            hq="San Francisco",
            employee_count="500",
            total_funding="$50M",
        ),
        review_sites=[
            ReviewSiteData(site_name="capterra", rating=4.3, review_count=200),
            ReviewSiteData(site_name="trustpilot", rating=3.1, review_count=50),
        ],
    )


def _make_overview(name: str, with_enrichment: bool = True) -> CompanyOverview:
    overview = CompanyOverview(
        company_name=name,
        url=f"https://{name.lower()}.com",
        tagline=f"{name} tagline",
        categories=["SaaS"],
        top_offerings=[
            CompanyOfferingSummary(
                product_name=f"{name} Platform",
                category="SaaS",
                description=f"{name}'s core platform",
                key_features=["analytics"],
            )
        ],
    )
    if with_enrichment:
        overview.enrichment = _make_enrichment(name)
        overview.verified_claims = [
            VerifiedClaim(claim="Has analytics", status="verified", external_source=ExternalSource.G2),
            VerifiedClaim(claim="Is free", status="contradicted", evidence="Paid plans exist"),
            VerifiedClaim(claim="Has API", status="unverified"),
        ]
    return overview


def _make_benchmark_result(with_enrichment: bool = True) -> MultiCompanyBenchmarkResult:
    return MultiCompanyBenchmarkResult(
        main_company="Acme",
        competitors=["BetaCo"],
        company_overviews={
            "Acme": _make_overview("Acme", with_enrichment),
            "BetaCo": _make_overview("BetaCo", with_enrichment),
        },
        evaluations=[
            MultiCompanyPromptEvaluation(
                prompt_id="p1",
                prompt_text="Compare Acme and BetaCo",
                category="comparison",
                llm_response="Acme is great.",
                winner="Acme",
                factual_accuracy=0.7,
                facts_confirmed=["Has analytics"],
                facts_wrong=["Is free"],
                facts_hallucinated=["Has 10K customers"],
                knowledge_gaps=["Pricing not mentioned"],
            ),
            MultiCompanyPromptEvaluation(
                prompt_id="p2",
                prompt_text="Which is better for teams?",
                category="recommendation",
                llm_response="BetaCo is simpler.",
                winner="BetaCo",
                factual_accuracy=0.5,
                facts_confirmed=[],
                facts_wrong=[],
                facts_hallucinated=["BetaCo has 5K users"],
                knowledge_gaps=[],
            ),
        ],
        summary=MultiCompanyBenchmarkSummary(
            companies=["Acme", "BetaCo"],
            total_prompts=2,
            company_stats=[
                MultiCompanyStats(
                    company_name="Acme",
                    wins=1,
                    avg_sentiment=0.6,
                    avg_factual_accuracy=0.6,
                    total_hallucinations=2,
                ),
                MultiCompanyStats(
                    company_name="BetaCo",
                    wins=1,
                    avg_sentiment=0.4,
                    avg_factual_accuracy=0.6,
                    total_hallucinations=2,
                ),
            ],
        ),
        enriched_profiles={
            "Acme": EnrichedCompanyProfile(
                company_name="Acme",
                enrichment=_make_enrichment("Acme"),
            ),
            "BetaCo": EnrichedCompanyProfile(
                company_name="BetaCo",
                enrichment=_make_enrichment("BetaCo"),
            ),
        },
    )


# ── HTML Report: External Validation ─────────────────────────────────────


class TestHtmlExternalValidation:

    def test_renders_ratings_table(self):
        result = _make_benchmark_result()
        html = _render_external_validation(result, ["Acme", "BetaCo"])

        assert "External Validation" in html
        assert "4.5/5" in html  # G2 rating
        assert "4.3" in html  # capterra
        assert "3.1" in html  # trustpilot

    def test_renders_company_facts(self):
        result = _make_benchmark_result()
        html = _render_external_validation(result, ["Acme", "BetaCo"])

        assert "2015" in html  # founded
        assert "San Francisco" in html  # HQ
        assert "$50M" in html  # funding

    def test_renders_g2_pros_cons(self):
        result = _make_benchmark_result()
        html = _render_external_validation(result, ["Acme", "BetaCo"])

        assert "Easy to use" in html
        assert "Expensive" in html

    def test_renders_verified_claims_badges(self):
        result = _make_benchmark_result()
        html = _render_external_validation(result, ["Acme", "BetaCo"])

        assert "verified" in html.lower()
        assert "contradicted" in html.lower()

    def test_returns_empty_without_enrichment(self):
        result = _make_benchmark_result(with_enrichment=False)
        html = _render_external_validation(result, ["Acme", "BetaCo"])

        assert html == ""


# ── HTML Report: Fact-Check Scorecard ────────────────────────────────────


class TestHtmlFactCheckSection:

    def test_renders_accuracy_score(self):
        result = _make_benchmark_result()
        html = _render_fact_check_section(result, ["Acme", "BetaCo"])

        assert "Fact-Check Scorecard" in html
        assert "60%" in html  # (0.7 + 0.5) / 2 = 0.6 = 60%

    def test_renders_hallucination_count(self):
        result = _make_benchmark_result()
        html = _render_fact_check_section(result, ["Acme", "BetaCo"])

        assert "Hallucinations" in html
        # 2 total hallucinations across evaluations
        assert ">2<" in html

    def test_renders_confirmed_count(self):
        result = _make_benchmark_result()
        html = _render_fact_check_section(result, ["Acme", "BetaCo"])

        assert "Facts Confirmed" in html

    def test_renders_top_hallucinations(self):
        result = _make_benchmark_result()
        html = _render_fact_check_section(result, ["Acme", "BetaCo"])

        assert "10K customers" in html
        assert "5K users" in html

    def test_returns_empty_without_fact_checks(self):
        result = _make_benchmark_result()
        for e in result.evaluations:
            e.factual_accuracy = 0.0
        html = _render_fact_check_section(result, ["Acme", "BetaCo"])

        assert html == ""


# ── HTML Report: Full Integration ────────────────────────────────────────


class TestHtmlReportIntegration:

    def test_full_report_contains_all_sections(self):
        result = _make_benchmark_result()
        html = generate_html_report(result)

        assert "External Validation" in html
        assert "Fact-Check Scorecard" in html
        assert "Scorecard" in html
        assert "Companies" in html

    def test_full_report_without_enrichment(self):
        result = _make_benchmark_result(with_enrichment=False)
        for e in result.evaluations:
            e.factual_accuracy = 0.0
        html = generate_html_report(result)

        # Should still generate without errors
        assert "Companies" in html
        assert "Scorecard" in html
        # No enrichment data sections (the section-title won't appear)
        assert "G2" not in html or "4.5/5" not in html


# ── Verifier ─────────────────────────────────────────────────────────────


class TestVerifierParsing:

    def test_parses_valid_json(self):
        response = json.dumps([
            {"claim": "Has API", "status": "verified", "evidence": "Confirmed", "external_source": "g2"},
            {"claim": "Free tier", "status": "contradicted", "evidence": "Paid only", "external_source": None},
        ])
        claims = _parse_verification_response(response)

        assert len(claims) == 2
        assert claims[0].status == "verified"
        assert claims[0].external_source == ExternalSource.G2
        assert claims[1].status == "contradicted"
        assert claims[1].external_source is None

    def test_parses_markdown_fenced_json(self):
        response = "```json\n" + json.dumps([
            {"claim": "Has API", "status": "verified", "evidence": "Yes", "external_source": "g2"}
        ]) + "\n```"
        claims = _parse_verification_response(response)

        assert len(claims) == 1
        assert claims[0].status == "verified"

    def test_returns_empty_on_invalid_json(self):
        claims = _parse_verification_response("not valid json at all")
        assert claims == []

    def test_returns_empty_on_empty_string(self):
        claims = _parse_verification_response("")
        assert claims == []


class FakeLLMForVerifier(LLMClient):
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps([
            {"claim": "Has analytics", "status": "verified", "evidence": "G2 confirms", "external_source": "g2"},
            {"claim": "Is free", "status": "contradicted", "evidence": "Paid plans", "external_source": "g2"},
        ])


class FakeLLMThatFails(LLMClient):
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("LLM timeout")


class TestVerifierIntegration:

    @pytest.mark.asyncio
    async def test_verifies_claims_with_enrichment(self):
        llm = FakeLLMForVerifier()
        enrichment = _make_enrichment("Acme")
        claims = ["Has analytics", "Is free"]

        result = await verify_claims(llm, "Acme", claims, enrichment)

        assert len(result) == 2
        assert result[0].status == "verified"
        assert result[1].status == "contradicted"

    @pytest.mark.asyncio
    async def test_skips_llm_when_no_evidence(self):
        llm = FakeLLMThatFails()  # Would throw if called
        enrichment = EnrichmentResult(company_name="Acme")
        claims = ["Has analytics"]

        result = await verify_claims(llm, "Acme", claims, enrichment)

        assert len(result) == 1
        assert result[0].status == "unverified"

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_claims(self):
        llm = FakeLLMForVerifier()
        enrichment = _make_enrichment("Acme")

        result = await verify_claims(llm, "Acme", [], enrichment)

        assert result == []

    @pytest.mark.asyncio
    async def test_graceful_on_llm_failure(self):
        llm = FakeLLMThatFails()
        enrichment = _make_enrichment("Acme")
        claims = ["Has analytics", "Is free"]

        result = await verify_claims(llm, "Acme", claims, enrichment)

        assert len(result) == 2
        assert all(c.status == "unverified" for c in result)


# ── Enrichment Client ────────────────────────────────────────────────────


class TestSnakeKeys:

    def test_converts_camel_to_snake(self):
        data = {
            "companyName": "Acme",
            "reviewCount": 100,
            "g2Url": "https://g2.com/acme",
        }
        result = _snake_keys(data)

        assert result["company_name"] == "Acme"
        assert result["review_count"] == 100
        assert result["g2_url"] == "https://g2.com/acme"

    def test_converts_nested_dicts(self):
        data = {
            "g2": {"reviewCount": 50, "prosThemes": []},
        }
        result = _snake_keys(data)

        assert result["g2"]["review_count"] == 50
        assert result["g2"]["pros_themes"] == []

    def test_converts_lists_of_dicts(self):
        data = {
            "reviewSites": [
                {"siteName": "capterra", "reviewCount": 200},
                {"siteName": "trustpilot", "reviewCount": 50},
            ]
        }
        result = _snake_keys(data)

        assert result["review_sites"][0]["site_name"] == "capterra"
        assert result["review_sites"][1]["site_name"] == "trustpilot"

    def test_preserves_unknown_keys(self):
        data = {"unknown_key": "value", "another": 42}
        result = _snake_keys(data)

        assert result["unknown_key"] == "value"
        assert result["another"] == 42

    def test_handles_empty_dict(self):
        assert _snake_keys({}) == {}


class TestFetchEnrichmentClient:

    @pytest.mark.asyncio
    async def test_returns_empty_on_connection_error(self):
        result = await fetch_enrichment("Acme", "https://acme.com", "http://localhost:99999")

        assert result.company_name == "Acme"
        assert result.g2 is None
        assert result.crunchbase is None

    @pytest.mark.asyncio
    async def test_returns_empty_on_invalid_url(self):
        result = await fetch_enrichment("Acme", "https://acme.com", "not-a-url")

        assert result.company_name == "Acme"
        assert result.g2 is None


# ── Markdown Report ──────────────────────────────────────────────────────


class TestMarkdownReport:

    def test_includes_external_validation_section(self):
        from falcon_iq_analyzer.services.multi_benchmark_service import generate_multi_benchmark_report

        result = _make_benchmark_result()
        md = generate_multi_benchmark_report(result)

        assert "## External Validation" in md
        assert "4.5/5" in md
        assert "Capterra" in md or "capterra" in md

    def test_includes_fact_check_section(self):
        from falcon_iq_analyzer.services.multi_benchmark_service import generate_multi_benchmark_report

        result = _make_benchmark_result()
        md = generate_multi_benchmark_report(result)

        assert "## Fact-Check Scorecard" in md
        assert "factual accuracy" in md.lower()
        assert "hallucination" in md.lower()

    def test_no_enrichment_sections_without_data(self):
        from falcon_iq_analyzer.services.multi_benchmark_service import generate_multi_benchmark_report

        result = _make_benchmark_result(with_enrichment=False)
        for e in result.evaluations:
            e.factual_accuracy = 0.0
        md = generate_multi_benchmark_report(result)

        assert "## External Validation" not in md
        assert "## Fact-Check Scorecard" not in md
