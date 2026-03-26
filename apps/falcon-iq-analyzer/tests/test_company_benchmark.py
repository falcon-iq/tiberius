"""Tests for the N-company benchmark pipeline."""

from __future__ import annotations

import asyncio
import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.multi_benchmark_prompts import (
    MULTI_BENCHMARK_ANALYZE_SYSTEM,
    MULTI_BENCHMARK_GENERATE_SYSTEM,
    MULTI_BENCHMARK_SUMMARIZE_SYSTEM,
)
from falcon_iq_analyzer.models.company_benchmark import MultiCompanyBenchmarkResult
from falcon_iq_analyzer.storage.local_storage import LocalStorageService


# ---------------------------------------------------------------------------
# Fake LLM client — dispatches canned responses based on the system prompt
# ---------------------------------------------------------------------------


class FakeLLMClient(LLMClient):
    """Returns deterministic JSON for each pipeline step."""

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        # Prompt generation
        if "market research expert" in system_prompt.lower():
            return json.dumps(
                {
                    "prompts": [
                        {
                            "prompt_id": "p1",
                            "prompt_text": "Compare Acme Corp and BetaCo for CRM solutions",
                            "category": "comparison",
                            "intent": "Direct comparison of CRM tools",
                        },
                        {
                            "prompt_id": "p2",
                            "prompt_text": "Which is better for marketing automation, Acme Corp or BetaCo?",
                            "category": "recommendation",
                            "intent": "Recommendation for marketing automation",
                        },
                    ]
                }
            )

        # Neutral LLM evaluation (BENCHMARK_EVAL_SYSTEM = "You are a helpful assistant.")
        if system_prompt.strip() == "You are a helpful assistant.":
            return (
                "Acme Corp is a strong choice for CRM with robust analytics. "
                "BetaCo offers a simpler onboarding experience but fewer integrations."
            )

        # Analysis of LLM response
        if "competitive intelligence analyst" in system_prompt.lower() and "company_mentions" in system_prompt:
            return json.dumps(
                {
                    "company_mentions": {
                        "Acme Corp": {
                            "company_name": "Acme Corp",
                            "mentioned": True,
                            "rank_position": 1,
                            "sentiment": 0.7,
                            "strengths_mentioned": ["robust analytics", "good integrations"],
                            "weaknesses_mentioned": ["complex setup"],
                            "recommended": True,
                        },
                        "BetaCo": {
                            "company_name": "BetaCo",
                            "mentioned": True,
                            "rank_position": 2,
                            "sentiment": 0.4,
                            "strengths_mentioned": ["simple onboarding"],
                            "weaknesses_mentioned": ["fewer integrations"],
                            "recommended": False,
                        },
                    },
                    "winner": "Acme Corp",
                    "analysis_notes": "Acme Corp perceived more favorably overall",
                }
            )

        # Summarization
        if "competitive intelligence analyst" in system_prompt.lower() and "company_stats" in system_prompt:
            return json.dumps(
                {
                    "company_stats": [
                        {
                            "company_name": "Acme Corp",
                            "top_strengths": ["Strong analytics", "Good integrations"],
                            "top_weaknesses": ["Complex setup process"],
                        },
                        {
                            "company_name": "BetaCo",
                            "top_strengths": ["Easy onboarding"],
                            "top_weaknesses": ["Limited integrations"],
                        },
                    ],
                    "key_insights": [
                        "Acme Corp dominates in technical capabilities",
                        "BetaCo appeals to users seeking simplicity",
                    ],
                }
            )

        return "{}"


# ---------------------------------------------------------------------------
# Helper: fake MongoDB collections backed by in-memory dicts
# ---------------------------------------------------------------------------

REPORT_ID = str(ObjectId())
MAIN_CRAWL_ID = str(ObjectId())
COMP_CRAWL_ID = str(ObjectId())


def _make_analysis_result(company_name: str) -> dict:
    return {
        "company_name": company_name,
        "total_pages": 10,
        "filtered_pages": 5,
        "classification_summary": {"product": 3, "about": 2},
        "product_pages_analyzed": 3,
        "top_offerings": [
            {
                "rank": 1,
                "product_name": f"{company_name} CRM",
                "category": "CRM",
                "description": f"{company_name}'s flagship CRM product",
                "key_features": ["analytics", "integrations"],
                "key_benefits": ["increased sales"],
                "target_audience": "Enterprise",
                "selling_script": "",
                "evidence_summary": "Flagship CRM product with analytics and integrations",
                "confidence": 0.9,
            }
        ],
        "markdown_report": f"# {company_name} Analysis",
    }


def _build_fake_mongo(storage: LocalStorageService) -> MagicMock:
    """Build a MongoClient mock with in-memory documents and real storage files."""
    # Persist analysis results to local storage so the pipeline can load them
    main_analysis_key = f"{MAIN_CRAWL_ID}/reports/result.json"
    comp_analysis_key = f"{COMP_CRAWL_ID}/reports/result.json"
    storage.save_file(main_analysis_key, json.dumps(_make_analysis_result("Acme Corp")))
    storage.save_file(comp_analysis_key, json.dumps(_make_analysis_result("BetaCo")))

    report_doc = {
        "_id": ObjectId(REPORT_ID),
        "companyCrawlDetailId": MAIN_CRAWL_ID,
        "competitionCrawlDetailIds": [COMP_CRAWL_ID],
        "status": "NOT_STARTED",
    }

    crawl_docs = {
        MAIN_CRAWL_ID: {
            "_id": ObjectId(MAIN_CRAWL_ID),
            "analysisResultsPath": main_analysis_key,
        },
        COMP_CRAWL_ID: {
            "_id": ObjectId(COMP_CRAWL_ID),
            "analysisResultsPath": comp_analysis_key,
        },
    }

    # Track status updates for assertions
    status_updates: list[dict] = []

    def make_collection(name: str) -> MagicMock:
        col = MagicMock()

        if name == "company_benchmark_report":

            def find_one(query):
                oid = query.get("_id")
                if oid and str(oid) == REPORT_ID:
                    return dict(report_doc)
                return None

            def update_one(query, update):
                new_vals = update.get("$set", {})
                status_updates.append(new_vals)
                report_doc.update(new_vals)

            col.find_one = MagicMock(side_effect=find_one)
            col.update_one = MagicMock(side_effect=update_one)

        elif name == "website_crawl_detail":

            def find_one(query):
                oid = query.get("_id")
                return crawl_docs.get(str(oid))

            col.find_one = MagicMock(side_effect=find_one)

        return col

    # Build mock client -> db -> collection chain
    mock_client = MagicMock()
    db_mock = MagicMock()
    db_mock.__getitem__ = MagicMock(side_effect=make_collection)
    mock_client.__getitem__ = MagicMock(return_value=db_mock)

    # Attach test helpers
    mock_client._status_updates = status_updates
    mock_client._report_doc = report_doc

    return mock_client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    from falcon_iq_analyzer.main import app

    return TestClient(app)


class TestCompanyBenchmarkEndpointValidation:
    """Test POST /company-benchmark input validation."""

    def test_returns_503_when_mongo_not_configured(self, client):
        with patch("falcon_iq_analyzer.routers.company_benchmark.settings") as mock_settings:
            mock_settings.mongo_uri = ""
            resp = client.post(
                "/company-benchmark",
                json={"companyBenchmarkReportId": str(ObjectId())},
            )
        assert resp.status_code == 503

    def test_returns_404_when_report_not_found(self, client):
        mock_client = MagicMock()
        mock_col = MagicMock()
        mock_col.find_one.return_value = None
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client.__getitem__ = MagicMock(return_value=mock_db)

        with (
            patch("falcon_iq_analyzer.routers.company_benchmark.settings") as mock_settings,
            patch("falcon_iq_analyzer.routers.company_benchmark.MongoClient", return_value=mock_client),
        ):
            mock_settings.mongo_uri = "mongodb://fake:27017"
            resp = client.post(
                "/company-benchmark",
                json={"companyBenchmarkReportId": str(ObjectId())},
            )
        assert resp.status_code == 404

    def test_returns_400_when_crawl_detail_not_found(self, client):
        report_id = str(ObjectId())
        missing_crawl_id = str(ObjectId())

        report_doc = {
            "_id": ObjectId(report_id),
            "companyCrawlDetailId": missing_crawl_id,
            "competitionCrawlDetailIds": [],
        }

        def fake_find_one(query):
            oid = str(query.get("_id"))
            if oid == report_id:
                return report_doc
            return None  # crawl detail not found

        mock_col = MagicMock()
        mock_col.find_one = MagicMock(side_effect=fake_find_one)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client = MagicMock()
        mock_client.__getitem__ = MagicMock(return_value=mock_db)

        with (
            patch("falcon_iq_analyzer.routers.company_benchmark.settings") as mock_settings,
            patch("falcon_iq_analyzer.routers.company_benchmark.MongoClient", return_value=mock_client),
        ):
            mock_settings.mongo_uri = "mongodb://fake:27017"
            resp = client.post(
                "/company-benchmark",
                json={"companyBenchmarkReportId": report_id},
            )
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"].lower()


class TestCompanyBenchmarkEndpointAccepted:
    """Test that a valid request returns 202."""

    def test_returns_202_with_correct_shape(self, client):
        report_id = str(ObjectId())
        main_crawl = str(ObjectId())
        comp_crawl = str(ObjectId())

        report_doc = {
            "_id": ObjectId(report_id),
            "companyCrawlDetailId": main_crawl,
            "competitionCrawlDetailIds": [comp_crawl],
        }

        crawl_docs = {
            main_crawl: {"_id": ObjectId(main_crawl), "analysisResultsPath": "x/result.json"},
            comp_crawl: {"_id": ObjectId(comp_crawl), "analysisResultsPath": "y/result.json"},
        }

        def fake_find_one(query):
            oid = str(query.get("_id"))
            if oid == report_id:
                return report_doc
            return crawl_docs.get(oid)

        mock_col = MagicMock()
        mock_col.find_one = MagicMock(side_effect=fake_find_one)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client = MagicMock()
        mock_client.__getitem__ = MagicMock(return_value=mock_db)

        with (
            patch("falcon_iq_analyzer.routers.company_benchmark.settings") as mock_settings,
            patch("falcon_iq_analyzer.routers.company_benchmark.MongoClient", return_value=mock_client),
            patch("falcon_iq_analyzer.routers.company_benchmark.asyncio") as mock_asyncio,
            patch("falcon_iq_analyzer.routers.company_benchmark.create_llm_client"),
        ):
            mock_settings.mongo_uri = "mongodb://fake:27017"
            resp = client.post(
                "/company-benchmark",
                json={"companyBenchmarkReportId": report_id, "num_prompts": 5},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["companyBenchmarkReportId"] == report_id
        assert data["status"] == "BENCHMARK_REPORT_IN_PROGRESS"
        assert "2" in data["message"]  # 2 companies
        mock_asyncio.create_task.assert_called_once()


class TestCompanyBenchmarkPipeline:
    """End-to-end test of run_company_benchmark() with mocked externals."""

    @pytest.mark.asyncio
    async def test_run_company_benchmark_pipeline(self):
        from falcon_iq_analyzer.pipeline.company_benchmark import run_company_benchmark

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageService(base_dir=tmpdir)
            fake_mongo = _build_fake_mongo(storage)
            fake_llm = FakeLLMClient()

            settings_mock = MagicMock()
            settings_mock.mongo_uri = "mongodb://fake:27017"
            settings_mock.storage_type = "local"
            settings_mock.results_dir = tmpdir

            with (
                patch(
                    "falcon_iq_analyzer.pipeline.company_benchmark.MongoClient",
                    return_value=fake_mongo,
                ),
                patch(
                    "falcon_iq_analyzer.pipeline.company_benchmark.create_storage_service",
                    return_value=storage,
                ),
            ):
                await run_company_benchmark(
                    company_benchmark_report_id=REPORT_ID,
                    num_prompts=2,
                    llm=fake_llm,
                    settings=settings_mock,
                )

            # --- Assertion 1: MongoDB status transitions ---
            updates = fake_mongo._status_updates
            statuses = [u["status"] for u in updates if "status" in u]
            assert statuses[0] == "BENCHMARK_REPORT_IN_PROGRESS"
            assert statuses[-1] == "COMPLETED"

            # --- Assertion 2: reportUrl was set ---
            final_update = updates[-1]
            assert "reportUrl" in final_update

            # --- Assertion 3: Markdown report exists and has expected sections ---
            md_key = f"company-benchmarks/benchmark-{REPORT_ID}.md"
            md_content = storage.load_file(md_key)
            assert md_content is not None, "Markdown report was not saved"
            assert "Acme Corp" in md_content
            assert "BetaCo" in md_content
            assert "Summary Scorecard" in md_content
            assert "LLM Perception" in md_content
            assert "Key Insights" in md_content
            assert "Detailed Evaluations" in md_content

            # --- Assertion 4: JSON result exists and deserializes correctly ---
            json_key = f"company-benchmarks/benchmark-{REPORT_ID}.json"
            json_content = storage.load_file(json_key)
            assert json_content is not None, "JSON result was not saved"

            result = MultiCompanyBenchmarkResult.model_validate_json(json_content)
            assert result.main_company == "Acme Corp"
            assert result.competitors == ["BetaCo"]
            assert len(result.prompts) == 2
            assert len(result.evaluations) == 2
            assert result.summary is not None
            assert result.summary.total_prompts == 2
            assert result.markdown_report != ""
