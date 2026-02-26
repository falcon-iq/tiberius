package com.falconiq.crawler.core;

import com.falconiq.crawler.storage.StorageService;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Manages concurrent crawl jobs.
 */
public class CrawlManager {

    private static final Logger logger = Logger.getLogger(CrawlManager.class.getName());
    private static CrawlManager instance;

    private final StorageService storageService;
    private final int maxConcurrentCrawls;
    private final ExecutorService executor;
    private final Map<String, CrawlJob> jobs = new ConcurrentHashMap<>();
    private final AtomicInteger activeCrawls = new AtomicInteger(0);
    private final CrawlProgressReporter progressReporter;

    private CrawlManager(StorageService storageService, int maxConcurrentCrawls,
                         CrawlProgressReporter progressReporter) {
        this.storageService = storageService;
        this.maxConcurrentCrawls = maxConcurrentCrawls;
        this.executor = Executors.newFixedThreadPool(maxConcurrentCrawls);
        this.progressReporter = progressReporter;
    }

    public static synchronized void initialize(StorageService storageService, int maxConcurrentCrawls,
                                               CrawlProgressReporter progressReporter) {
        instance = new CrawlManager(storageService, maxConcurrentCrawls, progressReporter);
    }

    public static CrawlManager getInstance() {
        if (instance == null) {
            throw new IllegalStateException("CrawlManager not initialized");
        }
        return instance;
    }

    /**
     * Start a crawl with MongoDB progress reporting.
     * websiteCrawlDetailId is used as the crawlId for storage.
     */
    public CrawlJob startCrawl(String url, int maxPages, int threads, long delayMs,
                               String websiteCrawlDetailId) {
        if (activeCrawls.get() >= maxConcurrentCrawls) {
            throw new IllegalStateException(
                    "Max concurrent crawls reached (" + maxConcurrentCrawls + ")");
        }

        String crawlId = websiteCrawlDetailId;
        AtomicInteger progressCounter = new AtomicInteger(0);
        CrawlJob job = new CrawlJob(crawlId, url, maxPages, progressCounter);
        jobs.put(crawlId, job);
        activeCrawls.incrementAndGet();

        executor.submit(() -> {
            try {
                WebCrawler crawler = new WebCrawler(
                        url, maxPages, threads, delayMs,
                        storageService, crawlId, progressCounter,
                        progressReporter, websiteCrawlDetailId);
                List<CrawlResult> results = crawler.crawl();
                job.complete(results);
                String crawledPagesPath = storageService.getBasePath(crawlId);
                progressReporter.reportCompleted(websiteCrawlDetailId, results.size(), crawledPagesPath);
                logger.info("Crawl " + crawlId + " completed with " + results.size() + " pages");
            } catch (Exception e) {
                logger.log(Level.SEVERE, "Crawl " + crawlId + " failed", e);
                job.fail(e.getMessage());
                progressReporter.reportFailed(websiteCrawlDetailId, e.getMessage());
            } finally {
                activeCrawls.decrementAndGet();
            }
        });

        return job;
    }

    public CrawlJob getJob(String crawlId) {
        return jobs.get(crawlId);
    }

    public int getActiveCrawlCount() {
        return activeCrawls.get();
    }

    public boolean isStorageHealthy() {
        return storageService.isHealthy();
    }
}
