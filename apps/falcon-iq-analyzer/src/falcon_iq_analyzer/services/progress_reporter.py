from __future__ import annotations

import logging
import time

from bson import ObjectId
from pymongo import MongoClient

logger = logging.getLogger(__name__)

DATABASE = "company_db"
COLLECTION = "website_crawl_detail"


class AnalysisProgressReporter:
    """Reports analysis progress to MongoDB.

    If mongo_uri is empty, all methods are no-ops.
    """

    def __init__(self, mongo_uri: str) -> None:
        if mongo_uri:
            self._client: MongoClient | None = MongoClient(mongo_uri)
            self._collection = self._client[DATABASE][COLLECTION]
            logger.info("AnalysisProgressReporter initialized with MongoDB")
        else:
            self._client = None
            self._collection = None
            logger.info("mongo_uri not set — analysis progress reporting disabled")

    def _update(self, website_crawl_detail_id: str, update: dict) -> None:
        if self._collection is None:
            return
        try:
            update["modifiedAt"] = int(time.time() * 1000)
            self._collection.update_one(
                {"_id": ObjectId(website_crawl_detail_id)},
                {"$set": update},
            )
        except Exception:
            logger.exception("Failed to update progress for %s", website_crawl_detail_id)

    def report_analyzer_in_progress(self, website_crawl_detail_id: str) -> None:
        self._update(website_crawl_detail_id, {"status": "ANALYZER_IN_PROGRESS"})

    def report_pages_analyzed(self, website_crawl_detail_id: str, pages_analyzed: int) -> None:
        self._update(website_crawl_detail_id, {"numberOfPagesAnalyzed": pages_analyzed})

    def report_step_progress(self, website_crawl_detail_id: str, step: str, message: str) -> None:
        self._update(website_crawl_detail_id, {"progress": f"{step}: {message}"})

    def report_completed(self, website_crawl_detail_id: str, analysis_results_path: str) -> None:
        if self._collection is None:
            return
        try:
            self._collection.update_one(
                {"_id": ObjectId(website_crawl_detail_id)},
                {
                    "$set": {
                        "status": "COMPLETED",
                        "analysisResultsPath": analysis_results_path,
                        "modifiedAt": int(time.time() * 1000),
                    },
                    "$unset": {"progress": ""},
                },
            )
        except Exception:
            logger.exception("Failed to report completion for %s", website_crawl_detail_id)

    def report_failed(self, website_crawl_detail_id: str, error: str) -> None:
        self._update(website_crawl_detail_id, {
            "status": "FAILED",
            "errorMessage": error,
        })
