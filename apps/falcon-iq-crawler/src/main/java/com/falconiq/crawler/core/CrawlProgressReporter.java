package com.falconiq.crawler.core;

import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Updates;
import org.bson.Document;
import org.bson.conversions.Bson;
import org.bson.types.ObjectId;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Fire-and-forget MongoDB updater for crawl progress.
 * If MONGO_URI is not set, returns a NoOpReporter that does nothing.
 */
public class CrawlProgressReporter {

    private static final Logger logger = Logger.getLogger(CrawlProgressReporter.class.getName());
    private static final String DATABASE = "company_db";
    private static final String COLLECTION = "website_crawl_detail";

    private final MongoClient mongoClient;
    private final ExecutorService executor;

    private CrawlProgressReporter(MongoClient mongoClient) {
        this.mongoClient = mongoClient;
        this.executor = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "crawl-progress-reporter");
            t.setDaemon(true);
            return t;
        });
    }

    /**
     * Create a reporter. Returns a NoOpReporter if mongoUri is null or blank.
     */
    public static CrawlProgressReporter create(String mongoUri) {
        if (mongoUri == null || mongoUri.isBlank()) {
            logger.info("MONGO_URI not set — crawl progress reporting disabled");
            return new NoOpReporter();
        }
        try {
            MongoClient client = MongoClients.create(mongoUri);
            logger.info("CrawlProgressReporter initialized with MongoDB");
            return new CrawlProgressReporter(client);
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to create MongoDB client — progress reporting disabled", e);
            return new NoOpReporter();
        }
    }

    public void reportPageCrawled(String websiteCrawlDetailId, int pagesCrawled) {
        if (websiteCrawlDetailId == null) return;
        executor.submit(() -> {
            try {
                MongoCollection<Document> collection = getCollection();
                Bson filter = Filters.eq("_id", new ObjectId(websiteCrawlDetailId));
                Bson update = Updates.combine(
                        Updates.set("numberOfPagesCrawled", (long) pagesCrawled),
                        Updates.set("modifiedAt", System.currentTimeMillis()));
                collection.updateOne(filter, update);
            } catch (Exception e) {
                logger.log(Level.WARNING, "Failed to report page crawled for " + websiteCrawlDetailId, e);
            }
        });
    }

    public void reportCompleted(String websiteCrawlDetailId, int totalPages, String crawledPagesPath) {
        if (websiteCrawlDetailId == null) return;
        executor.submit(() -> {
            try {
                MongoCollection<Document> collection = getCollection();
                Bson filter = Filters.eq("_id", new ObjectId(websiteCrawlDetailId));
                Bson update = Updates.combine(
                        Updates.set("status", "CRAWLING_COMPLETED"),
                        Updates.set("totalPages", (long) totalPages),
                        Updates.set("numberOfPagesCrawled", (long) totalPages),
                        Updates.set("crawledPagesPath", crawledPagesPath),
                        Updates.set("modifiedAt", System.currentTimeMillis()));
                collection.updateOne(filter, update);
                logger.info("Reported crawl completed for " + websiteCrawlDetailId
                        + " with " + totalPages + " pages");
            } catch (Exception e) {
                logger.log(Level.WARNING, "Failed to report completion for " + websiteCrawlDetailId, e);
            }
        });
    }

    public void reportFailed(String websiteCrawlDetailId, String error) {
        if (websiteCrawlDetailId == null) return;
        executor.submit(() -> {
            try {
                MongoCollection<Document> collection = getCollection();
                Bson filter = Filters.eq("_id", new ObjectId(websiteCrawlDetailId));
                Bson update = Updates.combine(
                        Updates.set("status", "FAILED"),
                        Updates.set("errorMessage", error),
                        Updates.set("modifiedAt", System.currentTimeMillis()));
                collection.updateOne(filter, update);
                logger.info("Reported crawl failed for " + websiteCrawlDetailId);
            } catch (Exception e) {
                logger.log(Level.WARNING, "Failed to report failure for " + websiteCrawlDetailId, e);
            }
        });
    }

    public void shutdown() {
        executor.shutdown();
        try {
            executor.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        if (mongoClient != null) {
            mongoClient.close();
        }
    }

    private MongoCollection<Document> getCollection() {
        return mongoClient.getDatabase(DATABASE).getCollection(COLLECTION);
    }

    /**
     * No-op implementation when MongoDB is not available.
     */
    private static class NoOpReporter extends CrawlProgressReporter {
        NoOpReporter() {
            super(null);
        }

        @Override
        public void reportPageCrawled(String websiteCrawlDetailId, int pagesCrawled) {
            // no-op
        }

        @Override
        public void reportCompleted(String websiteCrawlDetailId, int totalPages, String crawledPagesPath) {
            // no-op
        }

        @Override
        public void reportFailed(String websiteCrawlDetailId, String error) {
            // no-op
        }

        @Override
        public void shutdown() {
            // no-op
        }
    }
}
