package com.falconiq.crawler.core;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Tracks the state of an active or completed crawl job.
 */
public class CrawlJob {

    private final String id;
    private final String url;
    private final int maxPages;
    private final long startedAt;
    private final AtomicInteger pagesDownloaded;
    private volatile String status = "RUNNING";
    private volatile Long completedAt;
    private volatile List<CrawlResult> results;
    private volatile String error;

    public CrawlJob(String id, String url, int maxPages, AtomicInteger pagesDownloaded) {
        this.id = id;
        this.url = url;
        this.maxPages = maxPages;
        this.startedAt = System.currentTimeMillis();
        this.pagesDownloaded = pagesDownloaded;
    }

    public void complete(List<CrawlResult> results) {
        this.results = results;
        this.completedAt = System.currentTimeMillis();
        this.status = "COMPLETED";
    }

    public void fail(String error) {
        this.error = error;
        this.completedAt = System.currentTimeMillis();
        this.status = "FAILED";
    }

    public String getId() { return id; }
    public String getUrl() { return url; }
    public int getMaxPages() { return maxPages; }
    public String getStatus() { return status; }
    public int getPagesDownloaded() { return pagesDownloaded.get(); }
    public long getStartedAt() { return startedAt; }
    public Long getCompletedAt() { return completedAt; }
    public List<CrawlResult> getResults() { return results; }
    public String getError() { return error; }
}
