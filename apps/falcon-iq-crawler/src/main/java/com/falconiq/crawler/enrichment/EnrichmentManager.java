package com.falconiq.crawler.enrichment;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mongodb.client.MongoCollection;
import org.bson.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.*;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Singleton orchestrator for external enrichment.
 * Checks MongoDB cache first, fetches from external APIs on cache miss,
 * and stores results back in cache.
 */
public class EnrichmentManager {

    private static final Logger logger = Logger.getLogger(EnrichmentManager.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();

    private static EnrichmentManager instance;

    private final EnrichmentCache cache;
    private final G2Fetcher g2Fetcher;
    private final CrunchbaseFetcher crunchbaseFetcher;
    private final GoogleSearchFetcher googleSearchFetcher;
    private final ReviewSiteFetcher reviewSiteFetcher;
    private final String serpApiKey;
    private final ExecutorService executor;

    private EnrichmentManager(MongoCollection<Document> cacheCollection,
                              Map<String, Integer> ttlConfig,
                              String serpApiKey,
                              String analyzerApiUrl) {
        this.cache = new EnrichmentCache(cacheCollection, ttlConfig);
        this.g2Fetcher = new G2Fetcher(analyzerApiUrl);
        this.crunchbaseFetcher = new CrunchbaseFetcher();
        this.googleSearchFetcher = new GoogleSearchFetcher();
        this.reviewSiteFetcher = new ReviewSiteFetcher();
        this.serpApiKey = serpApiKey;
        this.executor = Executors.newFixedThreadPool(4, r -> {
            Thread t = new Thread(r, "enrichment-worker");
            t.setDaemon(true);
            return t;
        });
    }

    public static void initialize(MongoCollection<Document> cacheCollection,
                                  Map<String, Integer> ttlConfig,
                                  String serpApiKey,
                                  String analyzerApiUrl) {
        instance = new EnrichmentManager(cacheCollection, ttlConfig, serpApiKey, analyzerApiUrl);
        logger.info("EnrichmentManager initialized (serpApiKey="
                + (serpApiKey != null && !serpApiKey.isBlank() ? "set" : "not set")
                + ")");
    }

    public static EnrichmentManager getInstance() {
        return instance;
    }

    /**
     * Enrich a company with external data. Checks cache first, fetches on miss.
     * All sources run in parallel; failures are logged and skipped.
     */
    public EnrichmentResult enrich(String companyName, String companyUrl) {
        EnrichmentResult result = new EnrichmentResult(companyName);
        result.setFetchedAt(Instant.now().toString());
        boolean allCached = true;

        // Submit all four fetches in parallel
        Future<G2Data> g2Future = executor.submit(() -> fetchOrCache(companyName, "g2", G2Data.class,
                () -> g2Fetcher.fetch(companyName, serpApiKey)));
        Future<CrunchbaseData> cbFuture = executor.submit(() -> fetchOrCache(companyName, "crunchbase", CrunchbaseData.class,
                () -> crunchbaseFetcher.fetch(companyName, serpApiKey)));
        Future<List<GoogleSearchInsight>> gsFuture = executor.submit(() -> fetchOrCacheList(companyName, "google_search",
                () -> googleSearchFetcher.fetch(companyName, serpApiKey)));
        Future<List<ReviewSiteData>> rsFuture = executor.submit(() ->
                reviewSiteFetcher.fetch(companyName, serpApiKey));

        // Collect results with timeouts
        try {
            G2Data g2 = g2Future.get(45, TimeUnit.SECONDS);
            result.setG2(g2);
        } catch (Exception e) {
            logger.log(Level.WARNING, "G2 enrichment failed for " + companyName, e);
        }

        try {
            CrunchbaseData cb = cbFuture.get(30, TimeUnit.SECONDS);
            result.setCrunchbase(cb);
        } catch (Exception e) {
            logger.log(Level.WARNING, "Crunchbase enrichment failed for " + companyName, e);
        }

        try {
            List<GoogleSearchInsight> gs = gsFuture.get(30, TimeUnit.SECONDS);
            result.setGoogleInsights(gs != null ? gs : List.of());
        } catch (Exception e) {
            logger.log(Level.WARNING, "Google Search enrichment failed for " + companyName, e);
        }

        try {
            List<ReviewSiteData> rs = rsFuture.get(30, TimeUnit.SECONDS);
            result.setReviewSites(rs != null ? rs : List.of());
        } catch (Exception e) {
            logger.log(Level.WARNING, "Review site enrichment failed for " + companyName, e);
        }

        // Build external facts summary
        result.setExternalFacts(buildExternalFacts(result));
        result.setCached(allCached);

        logger.info("Enrichment completed for " + companyName
                + " (g2=" + (result.getG2() != null)
                + ", crunchbase=" + (result.getCrunchbase() != null)
                + ", reviewSites=" + result.getReviewSites().size()
                + ", googleInsights=" + result.getGoogleInsights().size() + ")");

        return result;
    }

    /**
     * Check cache for a source; if miss, call fetcher and store result.
     */
    private <T> T fetchOrCache(String companyName, String source, Class<T> type, Callable<T> fetcher) {
        // Try cache first
        Optional<Document> cached = cache.getCached(companyName, source);
        if (cached.isPresent()) {
            try {
                logger.fine("Cache hit for " + companyName + "/" + source);
                return mapper.readValue(cached.get().toJson(), type);
            } catch (Exception e) {
                logger.log(Level.WARNING, "Failed to deserialize cached " + source + " data", e);
            }
        }

        // Cache miss — fetch from external API
        try {
            T data = fetcher.call();
            if (data != null) {
                String json = mapper.writeValueAsString(data);
                cache.put(companyName, source, Document.parse(json));
            }
            return data;
        } catch (Exception e) {
            logger.log(Level.WARNING, "Fetch failed for " + companyName + "/" + source, e);
            return null;
        }
    }

    @SuppressWarnings("unchecked")
    private List<GoogleSearchInsight> fetchOrCacheList(String companyName, String source,
                                                       Callable<List<GoogleSearchInsight>> fetcher) {
        // Try cache first
        Optional<Document> cached = cache.getCached(companyName, source);
        if (cached.isPresent()) {
            try {
                logger.fine("Cache hit for " + companyName + "/" + source);
                List<?> raw = cached.get().getList("items", Document.class);
                List<GoogleSearchInsight> items = new ArrayList<>();
                for (Object item : raw) {
                    items.add(mapper.readValue(((Document) item).toJson(), GoogleSearchInsight.class));
                }
                return items;
            } catch (Exception e) {
                logger.log(Level.WARNING, "Failed to deserialize cached " + source + " data", e);
            }
        }

        // Cache miss
        try {
            List<GoogleSearchInsight> data = fetcher.call();
            if (data != null && !data.isEmpty()) {
                String json = mapper.writeValueAsString(Map.of("items", data));
                cache.put(companyName, source, Document.parse(json));
            }
            return data;
        } catch (Exception e) {
            logger.log(Level.WARNING, "Fetch failed for " + companyName + "/" + source, e);
            return List.of();
        }
    }

    private List<ExternalFact> buildExternalFacts(EnrichmentResult result) {
        List<ExternalFact> facts = new ArrayList<>();

        if (result.getG2() != null) {
            G2Data g2 = result.getG2();
            if (g2.getRating() != null) {
                String url = g2.getG2Url().isEmpty() ? "https://g2.com" : g2.getG2Url();
                facts.add(new ExternalFact(
                        "G2 rating: " + g2.getRating() + "/5 (" + g2.getReviewCount() + " reviews)",
                        "g2", url));
            }
            if (!g2.getDescription().isEmpty()) {
                facts.add(new ExternalFact("G2 summary: " + g2.getDescription(), "g2",
                        g2.getG2Url().isEmpty() ? "https://g2.com" : g2.getG2Url()));
            }
        }

        for (ReviewSiteData rs : result.getReviewSites()) {
            if (rs.getRating() != null) {
                facts.add(new ExternalFact(
                        rs.getSiteName() + " rating: " + rs.getRating() + "/5"
                                + (rs.getReviewCount() > 0 ? " (" + rs.getReviewCount() + " reviews)" : ""),
                        "google_search", rs.getUrl()));
            }
        }

        if (result.getCrunchbase() != null) {
            CrunchbaseData cb = result.getCrunchbase();
            if (cb.getTotalFunding() != null) {
                facts.add(new ExternalFact(
                        "Total funding: " + cb.getTotalFunding(),
                        "crunchbase", "https://crunchbase.com"));
            }
            if (cb.getEmployeeCount() != null) {
                facts.add(new ExternalFact(
                        "Employee count: " + cb.getEmployeeCount(),
                        "crunchbase", "https://crunchbase.com"));
            }
            if (cb.getFounded() != null) {
                facts.add(new ExternalFact(
                        "Founded: " + cb.getFounded(),
                        "crunchbase", "https://crunchbase.com"));
            }
        }

        return facts;
    }

    public void shutdown() {
        executor.shutdown();
        try {
            executor.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
