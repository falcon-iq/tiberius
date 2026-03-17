from __future__ import annotations

import asyncio
import logging
import time

from bson import ObjectId
from pymongo import MongoClient

logger = logging.getLogger(__name__)

DATABASE = "company_db"
COLLECTION = "website_crawl_detail"
CONFIG_COLLECTION = "industry_benchmark_config"


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

    def check_and_trigger_industry_benchmark(self, website_crawl_detail_id: str) -> None:
        """Check if this crawl detail is part of an industry benchmark config.

        If all companies in the config are now done (COMPLETED or FAILED),
        trigger the industry benchmark pipeline automatically.
        """
        if self._client is None:
            return

        try:
            db = self._client[DATABASE]
            config_col = db[CONFIG_COLLECTION]
            crawl_col = db[COLLECTION]

            # Find any config that references this crawl detail ID
            config_doc = config_col.find_one({
                "companyTasks.crawlDetailId": website_crawl_detail_id,
                "status": "GENERATING",
            })
            if not config_doc:
                return

            slug = config_doc["slug"]
            tasks = config_doc.get("companyTasks", [])
            logger.info("Crawl %s is part of industry benchmark %s — checking if all done",
                        website_crawl_detail_id, slug)

            # Check if all crawl details in this config are terminal
            all_done = True
            for task in tasks:
                cid = task.get("crawlDetailId")
                if not cid:
                    continue
                crawl_doc = crawl_col.find_one({"_id": ObjectId(cid)})
                if not crawl_doc:
                    continue
                status = crawl_doc.get("status", "")
                if status not in ("COMPLETED", "FAILED", "CRAWLING_COMPLETED"):
                    all_done = False
                    break

            if not all_done:
                logger.info("Industry benchmark %s: not all crawls done yet", slug)
                return

            logger.info("Industry benchmark %s: all crawls done — triggering pipeline", slug)

            # Build companies list from the config tasks
            companies = []
            for task in tasks:
                companies.append({
                    "name": task.get("name", ""),
                    "url": task.get("url", ""),
                    "crawlDetailId": task.get("crawlDetailId", ""),
                })

            # Trigger the industry benchmark pipeline
            from falcon_iq_analyzer.config import settings as app_settings
            from falcon_iq_analyzer.llm.factory import create_llm_client
            from falcon_iq_analyzer.pipeline.industry_benchmark import run_industry_benchmark

            llm = create_llm_client(app_settings)
            asyncio.create_task(
                run_industry_benchmark(
                    slug=slug,
                    companies=companies,
                    llm=llm,
                    settings=app_settings,
                )
            )

        except Exception:
            logger.exception("Failed to check industry benchmark trigger for %s",
                             website_crawl_detail_id)
