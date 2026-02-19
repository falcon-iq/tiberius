import os
import tempfile

import pytest

from falcon_iq_analyzer.storage.local_storage import LocalStorageService


@pytest.fixture
def local_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield LocalStorageService(base_dir=tmpdir)


def test_save_and_load_file(local_storage):
    key = "test/file.txt"
    content = "hello world"
    local_storage.save_file(key, content)

    loaded = local_storage.load_file(key)
    assert loaded == content


def test_file_exists(local_storage):
    assert not local_storage.file_exists("nonexistent.txt")

    local_storage.save_file("exists.txt", "data")
    assert local_storage.file_exists("exists.txt")


def test_load_nonexistent_returns_none(local_storage):
    assert local_storage.load_file("does_not_exist.txt") is None


def test_list_files(local_storage):
    local_storage.save_file("reports/result-abc.json", '{"data": 1}')
    local_storage.save_file("reports/result-def.json", '{"data": 2}')
    local_storage.save_file("reports/report-abc.md", "# Report")

    files = local_storage.list_files("reports/result-*.json")
    assert len(files) == 2
    assert "reports/result-abc.json" in files
    assert "reports/result-def.json" in files


def test_is_healthy(local_storage):
    assert local_storage.is_healthy()
