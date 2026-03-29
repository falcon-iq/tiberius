"""Tests for enrichment integration into the benchmark pipeline.

Covers:
- Context block enrichment injection
- Company order randomization (anti-bias)
- Fact-checking step
- Enrichment models serialization
"""

from __future__ import annotations

import json

import pytest

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.models.company_benchmark import (
    CompanyOfferingSummary,
    CompanyOverview,
    MultiCompanyPromptEvaluation,
    MultiCompanyStats,
)
from falcon_iq_analyzer.models.domain import AnalysisResult, GeneratedPrompt
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
from falcon_iq_analyzer.services.multi_benchmark_service import (
    _build_full_context,
    _build_ground_truth,
    _build_slim_context,
    evaluate_single_prompt_multi,
    generate_multi_prompts,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


def _make_analysis_result(name: str) -> AnalysisResult:
    return AnalysisResult(
        company_name=name,
        total_pages=10,
        filtered_pages=5,
        top_offerings=[
            {
                "rank": 1,
                "product_name": f"{name} Platform",
                "category": "SaaS",
                "description": f"{name}'s core platform for teams",
                "key_features": ["analytics", "integrations", "reporting"],
                "confidence": 0.9,
            }
        ],
    )


def _make_enrichment(name: str) -> EnrichmentResult:
    return EnrichmentResult(
        company_name=name,
        g2=G2Data(
            rating=4.5,
            review_count=1000,
            description=f"{name} is well-regarded by users",
            g2_url=f"https://g2.com/products/{name.lower()}",
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
        ],
        google_insights=[
            GoogleSearchInsight(
                query=f"{name} reviews",
                title=f"{name} Review",
                snippet="Great product",
                url="https://example.com",
                insight_type="review",
            )
        ],
    )


def _make_overview(name: str, with_enrichment: bool = True) -> CompanyOverview:
    overview = CompanyOverview(
        company_name=name,
        url=f"https://{name.lower()}.com",
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
            VerifiedClaim(claim=f"{name} has analytics", status="verified", external_source=ExternalSource.G2),
            VerifiedClaim(claim=f"{name} is free", status="contradicted", evidence="Pricing page shows paid plans"),
        ]
    return overview


# ── Context Block Tests ──────────────────────────────────────────────────


class TestSlimContext:
    """Test that slim context (injected into prompts) is short and realistic."""

    def test_includes_product_name_and_features(self):
        results = [_make_analysis_result("Acme")]
        block = _build_slim_context(results)

        assert "Acme Platform" in block
        assert "analytics" in block

    def test_includes_company_url(self):
        results = [_make_analysis_result("Acme")]
        overviews = {"Acme": _make_overview("Acme")}
        block = _build_slim_context(results, overviews)

        assert "acme.com" in block

    def test_does_not_include_enrichment(self):
        results = [_make_analysis_result("Acme")]
        overviews = {"Acme": _make_overview("Acme")}
        block = _build_slim_context(results, overviews)

        assert "[G2]" not in block
        assert "Founded" not in block
        assert "capterra" not in block

    def test_is_short(self):
        results = [_make_analysis_result("Acme"), _make_analysis_result("BetaCo")]
        block = _build_slim_context(results)

        assert len(block) < 1000, f"Slim context too long: {len(block)} chars"

    def test_multiple_companies(self):
        results = [_make_analysis_result("Acme"), _make_analysis_result("BetaCo")]
        block = _build_slim_context(results)

        assert "Acme" in block
        assert "BetaCo" in block


class TestFullContext:
    """Test that full context (for fact-checking) includes enrichment data."""

    def test_includes_g2_rating(self):
        results = [_make_analysis_result("Acme")]
        overviews = {"Acme": _make_overview("Acme")}
        block = _build_full_context(results, overviews)

        assert "4.5/5" in block
        assert "1000" in block

    def test_includes_company_data(self):
        results = [_make_analysis_result("Acme")]
        overviews = {"Acme": _make_overview("Acme")}
        block = _build_full_context(results, overviews)

        assert "2015" in block
        assert "San Francisco" in block

    def test_includes_verified_claims(self):
        results = [_make_analysis_result("Acme")]
        overviews = {"Acme": _make_overview("Acme")}
        block = _build_full_context(results, overviews)

        assert "Acme has analytics" in block

    def test_works_without_enrichment(self):
        results = [_make_analysis_result("Acme")]
        block = _build_full_context(results)

        assert "Acme" in block
        assert "[G2]" not in block


# ── Anti-Bias Tests ──────────────────────────────────────────────────────


class TestAntiBias:
    """Test that company ordering is randomized to prevent bias."""

    def test_context_block_order_varies(self):
        """Run multiple times and verify that company order is not always the same."""
        results = [
            _make_analysis_result("Alpha"),
            _make_analysis_result("Beta"),
            _make_analysis_result("Gamma"),
        ]

        orders_seen: set[str] = set()
        for _ in range(20):
            block = _build_slim_context(results)
            # Extract the order companies appear in
            order = []
            for name in ["Alpha", "Beta", "Gamma"]:
                pos = block.index(f"--- {name} ---")
                order.append((pos, name))
            order.sort()
            orders_seen.add(",".join(name for _, name in order))

        assert len(orders_seen) > 1, "Company order should vary across calls (randomized)"


# ── Ground Truth Builder Tests ───────────────────────────────────────────


class TestBuildGroundTruth:
    """Test the ground truth builder used for fact-checking."""

    def test_includes_g2_rating(self):
        overviews = {"Acme": _make_overview("Acme")}
        gt = _build_ground_truth(overviews)

        assert "4.5/5" in gt
        assert "1000" in gt

    def test_includes_company_facts(self):
        overviews = {"Acme": _make_overview("Acme")}
        gt = _build_ground_truth(overviews)

        assert "2015" in gt
        assert "San Francisco" in gt
        assert "$50M" in gt

    def test_includes_verified_claims(self):
        overviews = {"Acme": _make_overview("Acme")}
        gt = _build_ground_truth(overviews)

        assert "Acme has analytics" in gt
        assert "Verified" in gt

    def test_includes_contradicted_claims(self):
        overviews = {"Acme": _make_overview("Acme")}
        gt = _build_ground_truth(overviews)

        assert "Acme is free" in gt
        assert "Contradicted" in gt

    def test_empty_without_enrichment(self):
        overviews = {"Acme": _make_overview("Acme", with_enrichment=False)}
        gt = _build_ground_truth(overviews)

        assert gt.strip() == ""

    def test_multiple_companies(self):
        overviews = {
            "Acme": _make_overview("Acme"),
            "BetaCo": _make_overview("BetaCo"),
        }
        gt = _build_ground_truth(overviews)

        assert "Acme" in gt
        assert "BetaCo" in gt


# ── Enrichment Model Tests ───────────────────────────────────────────────


class TestEnrichmentModels:
    """Test enrichment model serialization/deserialization."""

    def test_enrichment_result_roundtrip(self):
        enr = _make_enrichment("Acme")
        data = json.loads(enr.model_dump_json())
        restored = EnrichmentResult(**data)

        assert restored.company_name == "Acme"
        assert restored.g2.rating == 4.5
        assert restored.crunchbase.founded == "2015"
        assert len(restored.review_sites) == 1
        assert len(restored.google_insights) == 1

    def test_verified_claim_roundtrip(self):
        claim = VerifiedClaim(
            claim="Has analytics",
            status="verified",
            evidence="Confirmed by G2",
            external_source=ExternalSource.G2,
        )
        data = json.loads(claim.model_dump_json())
        restored = VerifiedClaim(**data)

        assert restored.status == "verified"
        assert restored.external_source == ExternalSource.G2

    def test_enriched_profile_roundtrip(self):
        profile = EnrichedCompanyProfile(
            company_name="Acme",
            enrichment=_make_enrichment("Acme"),
            verified_claims=[
                VerifiedClaim(claim="Has API", status="verified"),
                VerifiedClaim(claim="Free tier", status="contradicted"),
            ],
        )
        data = json.loads(profile.model_dump_json())
        restored = EnrichedCompanyProfile(**data)

        assert restored.company_name == "Acme"
        assert len(restored.verified_claims) == 2

    def test_company_overview_with_enrichment(self):
        overview = _make_overview("Acme")
        data = json.loads(overview.model_dump_json())

        assert data["enrichment"]["g2"]["rating"] == 4.5
        assert data["enrichment"]["crunchbase"]["founded"] == "2015"
        assert len(data["verified_claims"]) == 2

    def test_evaluation_with_fact_check_fields(self):
        evaluation = MultiCompanyPromptEvaluation(
            prompt_id="p1",
            prompt_text="Compare Acme and BetaCo",
            category="comparison",
            factual_accuracy=0.75,
            facts_confirmed=["Acme has analytics"],
            facts_wrong=["BetaCo is free"],
            facts_hallucinated=["Acme has 10K customers"],
            knowledge_gaps=["Acme pricing not mentioned"],
        )
        data = json.loads(evaluation.model_dump_json())

        assert data["factual_accuracy"] == 0.75
        assert len(data["facts_confirmed"]) == 1
        assert len(data["facts_hallucinated"]) == 1

    def test_stats_with_accuracy_fields(self):
        stats = MultiCompanyStats(
            company_name="Acme",
            wins=5,
            avg_sentiment=0.6,
            avg_factual_accuracy=0.8,
            total_hallucinations=3,
        )
        data = json.loads(stats.model_dump_json())

        assert data["avg_factual_accuracy"] == 0.8
        assert data["total_hallucinations"] == 3


# ── Fact-Check Integration Tests ─────────────────────────────────────────


class FakeLLMForFactCheck(LLMClient):
    """Fake LLM that returns deterministic fact-check and analysis responses."""

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        # Eval prompt — return a response with some facts
        if "business technology advisor" in system_prompt.lower():
            return "Acme has great analytics and 10,000 customers. BetaCo is free to use."

        # Analysis of response
        if "competitive intelligence analyst" in system_prompt.lower() and "company_mentions" in system_prompt:
            return json.dumps({
                "company_mentions": {
                    "Acme": {
                        "company_name": "Acme",
                        "mentioned": True,
                        "sentiment": 0.5,
                        "strengths_mentioned": ["analytics"],
                        "weaknesses_mentioned": [],
                        "recommended": True,
                    },
                    "BetaCo": {
                        "company_name": "BetaCo",
                        "mentioned": True,
                        "sentiment": 0.3,
                        "strengths_mentioned": [],
                        "weaknesses_mentioned": [],
                        "recommended": False,
                    },
                },
                "winner": "Acme",
                "analysis_notes": "Acme mentioned more favorably",
            })

        # Fact-check response
        if "fact-checker" in system_prompt.lower():
            return json.dumps({
                "factual_accuracy": 0.5,
                "facts_confirmed": ["Acme has analytics"],
                "facts_wrong": ["BetaCo is free to use"],
                "facts_hallucinated": ["Acme has 10,000 customers"],
                "knowledge_gaps": ["Acme pricing not mentioned"],
            })

        return "{}"


class TestFactCheckIntegration:
    """Test that fact-checking runs during evaluation when enrichment is available."""

    @pytest.mark.asyncio
    async def test_evaluation_includes_fact_check(self):
        llm = FakeLLMForFactCheck()
        prompt = GeneratedPrompt(
            prompt_id="p1",
            prompt_text="Compare Acme and BetaCo for analytics",
            category="comparison",
            intent="analytics comparison",
        )
        overviews = {
            "Acme": _make_overview("Acme"),
            "BetaCo": _make_overview("BetaCo"),
        }

        result = await evaluate_single_prompt_multi(
            llm, prompt, ["Acme", "BetaCo"], overviews
        )

        assert result.factual_accuracy == 0.5
        assert "Acme has analytics" in result.facts_confirmed
        assert "Acme has 10,000 customers" in result.facts_hallucinated
        assert "BetaCo is free to use" in result.facts_wrong
        assert "Acme pricing not mentioned" in result.knowledge_gaps

    @pytest.mark.asyncio
    async def test_evaluation_without_enrichment(self):
        llm = FakeLLMForFactCheck()
        prompt = GeneratedPrompt(
            prompt_id="p1",
            prompt_text="Compare Acme and BetaCo",
            category="comparison",
            intent="general comparison",
        )

        result = await evaluate_single_prompt_multi(
            llm, prompt, ["Acme", "BetaCo"], company_overviews=None
        )

        # Without enrichment, fact-check fields should be empty/zero
        assert result.factual_accuracy == 0.0
        assert result.facts_confirmed == []
        assert result.facts_hallucinated == []


# ── Prompt Generation Anti-Bias Tests ────────────────────────────────────


class FakeLLMForPromptGen(LLMClient):
    """Fake LLM that returns prompts and captures the user prompt for inspection."""

    def __init__(self):
        self.captured_user_prompts: list[str] = []

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.captured_user_prompts.append(user_prompt)

        if "market research expert" in system_prompt.lower():
            return json.dumps({
                "prompts": [
                    {
                        "prompt_id": "p1",
                        "prompt_text": "Compare Alpha and Beta",
                        "category": "comparison",
                        "intent": "general comparison",
                        "prompt_type": "generic",
                    }
                ]
            })

        # Product grouping
        if "normalize" in system_prompt.lower() or "group" in system_prompt.lower():
            return json.dumps({"groups": []})

        return "{}"


class TestPromptGenerationAntiBias:
    """Test that prompt generation treats all companies equally."""

    @pytest.mark.asyncio
    async def test_no_main_competitor_language(self):
        llm = FakeLLMForPromptGen()
        main = _make_analysis_result("Alpha")
        competitors = [_make_analysis_result("Beta")]

        await generate_multi_prompts(llm, main, competitors, num_prompts=1)

        user_prompt = llm.captured_user_prompts[0]
        assert "Main Company" not in user_prompt, "Should not use 'Main Company' framing"
        assert "Competitors:" not in user_prompt, "Should not use 'Competitors' framing"
        assert "Companies being evaluated" in user_prompt

    @pytest.mark.asyncio
    async def test_all_companies_present(self):
        llm = FakeLLMForPromptGen()
        main = _make_analysis_result("Alpha")
        competitors = [_make_analysis_result("Beta"), _make_analysis_result("Gamma")]

        await generate_multi_prompts(llm, main, competitors, num_prompts=1)

        user_prompt = llm.captured_user_prompts[0]
        assert "Alpha" in user_prompt
        assert "Beta" in user_prompt
        assert "Gamma" in user_prompt

    @pytest.mark.asyncio
    async def test_equal_treatment_instruction(self):
        llm = FakeLLMForPromptGen()
        main = _make_analysis_result("Alpha")
        competitors = [_make_analysis_result("Beta")]

        await generate_multi_prompts(llm, main, competitors, num_prompts=1)

        user_prompt = llm.captured_user_prompts[0]
        assert "Treat all companies equally" in user_prompt
