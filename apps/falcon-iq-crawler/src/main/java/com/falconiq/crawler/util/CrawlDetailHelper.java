package com.falconiq.crawler.util;

import org.bson.Document;

public class CrawlDetailHelper {

    private static final long TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000L;

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
        return (System.currentTimeMillis() - modifiedAt) < TWENTY_FOUR_HOURS_MS;
    }
}
