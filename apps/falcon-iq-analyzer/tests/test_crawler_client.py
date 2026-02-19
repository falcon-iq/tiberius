import pytest

from falcon_iq_analyzer.pipeline.job_manager import JobManager


@pytest.fixture
def job_manager():
    return JobManager()


def test_get_output_dir_for_url():
    from falcon_iq_analyzer.services.crawler import get_output_dir_for_url

    result = get_output_dir_for_url("https://example.com/path")
    assert "example.com" in result


def test_get_output_dir_for_url_with_port():
    from falcon_iq_analyzer.services.crawler import get_output_dir_for_url

    result = get_output_dir_for_url("https://example.com:8443/path")
    # Colons should be replaced with underscores
    assert "example.com_8443" in result


def test_job_manager_create_and_get(job_manager):
    job = job_manager.create_job()
    assert job.status == "pending"
    assert job.job_id

    fetched = job_manager.get_job(job.job_id)
    assert fetched is not None
    assert fetched.job_id == job.job_id


def test_job_manager_update_status(job_manager):
    job = job_manager.create_job()
    job_manager.update_status(job.job_id, "running", "Crawling...")

    updated = job_manager.get_job(job.job_id)
    assert updated.status == "running"
    assert updated.progress == "Crawling..."


def test_job_manager_set_error(job_manager):
    job = job_manager.create_job()
    job_manager.set_error(job.job_id, "Something failed")

    updated = job_manager.get_job(job.job_id)
    assert updated.status == "failed"
    assert updated.error == "Something failed"


def test_job_manager_nonexistent_returns_none(job_manager):
    assert job_manager.get_job("nonexistent") is None
