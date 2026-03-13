package com.falconiq.crawler.util;

import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Sorts;
import org.bson.Document;

import java.util.logging.Logger;

public class CrawlDetailHelper {

    private static final Logger logger = Logger.getLogger(CrawlDetailHelper.class.getName());
    private static final long CACHE_TTL_MS = Long.parseLong(
            System.getenv().getOrDefault("CRAWL_CACHE_TTL_DAYS", "1")) * 24 * 60 * 60 * 1000L;

    private CrawlDetailHelper() {
    }

    public static boolean isAlreadyCompleted(Document detail) {
        String status = detail.getString("status");
        String analysisPath = detail.getString("analysisResultsPath");
        if (!"COMPLETED".equals(status) || analysisPath == null || analysisPath.isBlank()) {
            return false;
        }
        Long modifiedAt = detail.getLong("modifiedAt");
        if (modifiedAt == null) {
            return false;
        }
        return (System.currentTimeMillis() - modifiedAt) < CACHE_TTL_MS;
    }

    /**
     * Finds a recently completed WebsiteCrawlDetail for the same domain (within 24 hours).
     * Returns the document if found, null otherwise.
     */
    public static Document findRecentCompletedForDomain(MongoCollection<Document> collection, String websiteLink) {
        String normalized = UrlUtils.normalizeUrl(websiteLink);
        long cutoff = System.currentTimeMillis() - CACHE_TTL_MS;

        for (Document doc : collection.find(Filters.and(
                Filters.eq("status", "COMPLETED"),
                Filters.gte("modifiedAt", cutoff)))
                .sort(Sorts.descending("modifiedAt"))) {

            String docLink = doc.getString("websiteLink");
            String docAnalysisPath = doc.getString("analysisResultsPath");
            if (docLink != null && docAnalysisPath != null && !docAnalysisPath.isBlank()
                    && UrlUtils.normalizeUrl(docLink).equals(normalized)) {
                return doc;
            }
        }
        return null;
    }

}
