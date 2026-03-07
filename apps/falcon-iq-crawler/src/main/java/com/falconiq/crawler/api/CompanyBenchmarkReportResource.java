package com.falconiq.crawler.api;

import com.falconiq.crawler.core.CrawlJob;
import com.falconiq.crawler.core.CrawlManager;
import com.falconiq.crawler.core.CrawlProgressReporter;
import com.falconiq.crawler.util.CrawlDetailHelper;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Updates;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.bson.Document;
import org.bson.types.ObjectId;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.logging.Level;
import java.util.logging.Logger;

@Path("/company-benchmark-report")
public class CompanyBenchmarkReportResource {

    private static final Logger logger = Logger.getLogger(CompanyBenchmarkReportResource.class.getName());
    private static final String BENCHMARK_REPORT_COLLECTION = "company_benchmark_report";
    private static final String CRAWL_DETAIL_COLLECTION = "website_crawl_detail";
    private static final long POLL_INTERVAL_MS = 5000;
    private static final int DEFAULT_MAX_PAGES = 100;

    private final ExecutorService executor = Executors.newCachedThreadPool(r -> {
        Thread t = new Thread(r, "benchmark-processor");
        t.setDaemon(true);
        return t;
    });

    @POST
    @Path("/process")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response process(Map<String, Object> request) {
        String reportId = (String) request.get("companyBenchmarkReportId");
        if (reportId == null || reportId.isBlank()) {
            return Response.status(400)
                    .entity(Map.of("error", "companyBenchmarkReportId is required"))
                    .build();
        }

        CrawlManager manager = CrawlManager.getInstance();
        CrawlProgressReporter reporter = manager.getProgressReporter();
        MongoCollection<Document> reportCollection = reporter.getMongoCollection(BENCHMARK_REPORT_COLLECTION);
        if (reportCollection == null) {
            return Response.status(503)
                    .entity(Map.of("error", "MongoDB not available"))
                    .build();
        }

        // Verify the benchmark report exists
        Document reportDoc = reportCollection.find(Filters.eq("_id", new ObjectId(reportId))).first();
        if (reportDoc == null) {
            return Response.status(404)
                    .entity(Map.of("error", "CompanyBenchmarkReport not found: " + reportId))
                    .build();
        }

        // Return 202 immediately, process in background
        executor.submit(() -> processBenchmarkReport(reportId, reportDoc));

        return Response.status(202)
                .entity(Map.of(
                        "companyBenchmarkReportId", reportId,
                        "status", "PROCESSING",
                        "message", "Benchmark report processing started"))
                .build();
    }

    private void processBenchmarkReport(String reportId, Document reportDoc) {
        CrawlManager manager = CrawlManager.getInstance();
        CrawlProgressReporter reporter = manager.getProgressReporter();
        MongoCollection<Document> reportCollection = reporter.getMongoCollection(BENCHMARK_REPORT_COLLECTION);
        MongoCollection<Document> crawlDetailCollection = reporter.getMongoCollection(CRAWL_DETAIL_COLLECTION);

        try {
            // Update benchmark report status to CRAWL_IN_PROGRESS
            updateBenchmarkReportStatus(reportCollection, reportId, "CRAWL_IN_PROGRESS");

            String companyCrawlDetailId = reportDoc.getString("companyCrawlDetailId");
            List<String> competitionCrawlDetailIds = reportDoc.getList("competitionCrawlDetailIds", String.class,
                    new ArrayList<>());

            // Crawl the main company first
            logger.info("Benchmark " + reportId + ": starting crawl for company " + companyCrawlDetailId);
            boolean success = startAndWaitForCrawl(manager, crawlDetailCollection, companyCrawlDetailId);
            if (!success) {
                logger.warning("Benchmark " + reportId + ": company crawl failed for " + companyCrawlDetailId);
                updateBenchmarkReportStatus(reportCollection, reportId, "FAILED");
                return;
            }

            // Crawl each competitor one by one
            for (String competitorId : competitionCrawlDetailIds) {
                logger.info("Benchmark " + reportId + ": starting crawl for competitor " + competitorId);
                success = startAndWaitForCrawl(manager, crawlDetailCollection, competitorId);
                if (!success) {
                    logger.warning("Benchmark " + reportId + ": competitor crawl failed for " + competitorId);
                    updateBenchmarkReportStatus(reportCollection, reportId, "FAILED");
                    return;
                }
            }

            logger.info("Benchmark " + reportId + ": all crawls completed successfully");

            // Trigger the LLM benchmark on the analyzer
            triggerAnalyzerBenchmark(reportId);
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Benchmark " + reportId + ": processing failed", e);
            updateBenchmarkReportStatus(reportCollection, reportId, "FAILED");
        }
    }

    private boolean startAndWaitForCrawl(CrawlManager manager,
                                         MongoCollection<Document> crawlDetailCollection,
                                         String websiteCrawlDetailId) {
        // Read the WebsiteCrawlDetail to get the website URL
        Document detail = crawlDetailCollection.find(
                Filters.eq("_id", new ObjectId(websiteCrawlDetailId))).first();
        if (detail == null) {
            logger.warning("WebsiteCrawlDetail not found: " + websiteCrawlDetailId);
            return false;
        }

        if (CrawlDetailHelper.isAlreadyCompleted(detail)) {
            logger.info("WebsiteCrawlDetail " + websiteCrawlDetailId + " already completed — skipping crawl");
            return true;
        }

        String websiteLink = detail.getString("websiteLink");
        if (websiteLink == null || websiteLink.isBlank()) {
            logger.warning("WebsiteCrawlDetail " + websiteCrawlDetailId + " has no websiteLink");
            return false;
        }

        // Start the crawl
        CrawlJob job;
        try {
            job = manager.startCrawl(websiteLink, DEFAULT_MAX_PAGES, 5, 1000, websiteCrawlDetailId);
        } catch (IllegalStateException e) {
            logger.warning("Cannot start crawl for " + websiteCrawlDetailId + ": " + e.getMessage());
            return false;
        }

        // Poll until crawl completes or fails
        while (true) {
            String status = job.getStatus();
            if ("COMPLETED".equals(status)) {
                return true;
            }
            if ("FAILED".equals(status)) {
                logger.warning("Crawl failed for " + websiteCrawlDetailId + ": " + job.getError());
                return false;
            }
            try {
                Thread.sleep(POLL_INTERVAL_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                logger.warning("Polling interrupted for " + websiteCrawlDetailId);
                return false;
            }
        }
    }

    private void triggerAnalyzerBenchmark(String reportId) {
        String analyzerApiUrl = CrawlManager.getInstance().getAnalyzerApiUrl();
        if (analyzerApiUrl == null || analyzerApiUrl.isBlank()) {
            logger.info("ANALYZER_API_URL not set — skipping benchmark trigger for " + reportId);
            return;
        }
        try {
            String jsonBody = "{\"companyBenchmarkReportId\":\"" + reportId + "\"}";
            byte[] jsonBytes = jsonBody.getBytes(StandardCharsets.UTF_8);
            logger.info("Triggering analyzer benchmark for " + reportId);

            HttpURLConnection conn = (HttpURLConnection) URI.create(
                    analyzerApiUrl + "/company-benchmark").toURL().openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setRequestProperty("Content-Length", String.valueOf(jsonBytes.length));
            conn.setDoOutput(true);
            conn.setFixedLengthStreamingMode(jsonBytes.length);
            try (OutputStream os = conn.getOutputStream()) {
                os.write(jsonBytes);
                os.flush();
            }
            int status = conn.getResponseCode();
            String body = new String(
                    (status < 400 ? conn.getInputStream() : conn.getErrorStream()).readAllBytes(),
                    StandardCharsets.UTF_8);
            logger.info("Triggered analyzer benchmark for " + reportId
                    + " — response: " + status + " body: " + body);
            conn.disconnect();
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to trigger analyzer benchmark for " + reportId, e);
        }
    }

    private void updateBenchmarkReportStatus(MongoCollection<Document> collection,
                                             String reportId, String status) {
        try {
            collection.updateOne(
                    Filters.eq("_id", new ObjectId(reportId)),
                    Updates.combine(
                            Updates.set("status", status),
                            Updates.set("modifiedAt", System.currentTimeMillis())));
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to update benchmark report status for " + reportId, e);
        }
    }
}
