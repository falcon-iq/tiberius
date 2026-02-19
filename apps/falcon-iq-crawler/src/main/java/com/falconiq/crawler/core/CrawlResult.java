package com.falconiq.crawler.core;

/**
 * Represents the result of crawling a single page.
 */
public record CrawlResult(String url, String storagePath, int statusCode) {
}
