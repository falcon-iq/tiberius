import os

import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("WEB_ANALYZER_STORAGE_TYPE", "local")
    monkeypatch.setenv("WEB_ANALYZER_LLM_PROVIDER", "openai")
    monkeypatch.setenv("WEB_ANALYZER_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("WEB_ANALYZER_RESULTS_DIR", "/tmp/analyzer_test_results")
    monkeypatch.setenv("WEB_ANALYZER_CRAWLED_SITES_DIR", "/tmp/analyzer_test_crawled")
