package com.falconiq.crawler;

import com.falconiq.crawler.core.CrawlManager;
import com.falconiq.crawler.core.CrawlProgressReporter;
import com.falconiq.crawler.enrichment.EnrichmentManager;
import com.falconiq.crawler.storage.LocalStorageService;
import com.falconiq.crawler.storage.S3StorageService;
import com.falconiq.crawler.storage.StorageService;
import com.mongodb.client.MongoCollection;
import org.bson.Document;
import org.eclipse.jetty.ee10.servlet.ServletContextHandler;
import org.eclipse.jetty.ee10.servlet.ServletHolder;
import org.eclipse.jetty.server.Server;
import org.glassfish.jersey.servlet.ServletContainer;

import java.util.Map;
import java.util.logging.Logger;

public class Main {

    private static final Logger logger = Logger.getLogger(Main.class.getName());

    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(env("PORT", "8080"));
        int maxConcurrentCrawls = Integer.parseInt(env("MAX_CONCURRENT_CRAWLS", "3"));
        String storageType = env("STORAGE_TYPE", "local");

        StorageService storageService = createStorageService(storageType);

        String mongoUri = System.getenv("MONGO_URI");
        CrawlProgressReporter progressReporter = CrawlProgressReporter.create(mongoUri);
        String analyzerApiUrl = env("ANALYZER_API_URL", "");
        CrawlManager.initialize(storageService, maxConcurrentCrawls, progressReporter, analyzerApiUrl);

        // Initialize enrichment manager
        String serpApiKey = env("SERP_API_KEY", "");
        MongoCollection<Document> enrichmentCacheCollection = progressReporter.getMongoCollection("enrichment_cache");
        Map<String, Integer> ttlConfig = Map.of(
                "g2", Integer.parseInt(env("ENRICHMENT_TTL_G2_DAYS", "7")),
                "crunchbase", Integer.parseInt(env("ENRICHMENT_TTL_CRUNCHBASE_DAYS", "30")),
                "google_search", Integer.parseInt(env("ENRICHMENT_TTL_GOOGLE_DAYS", "3"))
        );
        EnrichmentManager.initialize(enrichmentCacheCollection, ttlConfig, serpApiKey, analyzerApiUrl);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("Shutting down services...");
            EnrichmentManager.getInstance().shutdown();
            progressReporter.shutdown();
        }));

        Server server = new Server(port);

        ServletContextHandler context = new ServletContextHandler();
        context.setContextPath("/");

        ServletHolder jerseyServlet = context.addServlet(
                ServletContainer.class, "/api/*");
        jerseyServlet.setInitOrder(1);
        jerseyServlet.setInitParameter(
                "jakarta.ws.rs.Application",
                "com.falconiq.crawler.AppConfig");

        server.setHandler(context);

        logger.info("Starting Falcon IQ Crawler on port " + port);
        logger.info("Storage type: " + storageType);
        server.start();
        logger.info("Server started at http://localhost:" + port);
        server.join();
    }

    private static StorageService createStorageService(String storageType) {
        return switch (storageType.toLowerCase()) {
            case "s3" -> {
                String bucket = System.getenv("S3_BUCKET_NAME");
                if (bucket == null || bucket.isBlank()) {
                    throw new IllegalArgumentException(
                            "S3_BUCKET_NAME is required when STORAGE_TYPE=s3");
                }
                String region = env("AWS_REGION", "us-east-1");
                logger.info("Using S3 storage: bucket=" + bucket + ", region=" + region);
                yield new S3StorageService(bucket, region);
            }
            case "local" -> {
                String outputDir = env("OUTPUT_DIR", "crawled_pages");
                logger.info("Using local storage: dir=" + outputDir);
                yield new LocalStorageService(outputDir);
            }
            default -> throw new IllegalArgumentException(
                    "Unknown STORAGE_TYPE: " + storageType);
        };
    }

    private static String env(String key, String defaultValue) {
        String value = System.getenv(key);
        return (value != null && !value.isBlank()) ? value : defaultValue;
    }
}
