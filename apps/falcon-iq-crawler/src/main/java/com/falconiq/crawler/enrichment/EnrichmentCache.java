package com.falconiq.crawler.enrichment;

import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.IndexOptions;
import com.mongodb.client.model.Indexes;
import com.mongodb.client.model.ReplaceOptions;
import org.bson.Document;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * MongoDB-backed cache for enrichment data with per-source TTL.
 *
 * <p>Documents are stored with a {@code ttlExpireAt} field that MongoDB's
 * TTL index automatically removes once expired.</p>
 */
public class EnrichmentCache {

    private static final Logger logger = Logger.getLogger(EnrichmentCache.class.getName());
    private static final String COLLECTION = "enrichment_cache";

    private final MongoCollection<Document> collection;
    private final Map<String, Integer> ttlDaysBySource;

    /**
     * @param collection        the MongoDB collection (may be null if Mongo is unavailable)
     * @param ttlDaysBySource   TTL in days per source, e.g. {"g2": 7, "crunchbase": 30, "google_search": 3}
     */
    public EnrichmentCache(MongoCollection<Document> collection, Map<String, Integer> ttlDaysBySource) {
        this.collection = collection;
        this.ttlDaysBySource = ttlDaysBySource;
        ensureTtlIndex();
    }

    /**
     * Look up cached enrichment data for a company + source.
     * Returns empty if no valid (non-expired) document exists.
     */
    public Optional<Document> getCached(String companyName, String source) {
        if (collection == null) return Optional.empty();
        try {
            Document doc = collection.find(
                    Filters.and(
                            Filters.eq("companyName", companyName.toLowerCase()),
                            Filters.eq("source", source),
                            Filters.gt("ttlExpireAt", new Date())
                    )
            ).first();
            return Optional.ofNullable(doc).map(d -> d.get("data", Document.class));
        } catch (Exception e) {
            logger.log(Level.WARNING, "Cache lookup failed for " + companyName + "/" + source, e);
            return Optional.empty();
        }
    }

    /**
     * Store enrichment data in the cache. Upserts by companyName + source.
     */
    public void put(String companyName, String source, Document data) {
        if (collection == null) return;
        try {
            int ttlDays = ttlDaysBySource.getOrDefault(source, 7);
            Instant expireAt = Instant.now().plus(ttlDays, ChronoUnit.DAYS);

            Document doc = new Document()
                    .append("companyName", companyName.toLowerCase())
                    .append("source", source)
                    .append("data", data)
                    .append("fetchedAt", new Date())
                    .append("ttlExpireAt", Date.from(expireAt));

            collection.replaceOne(
                    Filters.and(
                            Filters.eq("companyName", companyName.toLowerCase()),
                            Filters.eq("source", source)
                    ),
                    doc,
                    new ReplaceOptions().upsert(true)
            );
        } catch (Exception e) {
            logger.log(Level.WARNING, "Cache put failed for " + companyName + "/" + source, e);
        }
    }

    private void ensureTtlIndex() {
        if (collection == null) return;
        try {
            collection.createIndex(
                    Indexes.ascending("ttlExpireAt"),
                    new IndexOptions().expireAfter(0L, TimeUnit.SECONDS)
            );
            // Compound index for fast lookups
            collection.createIndex(
                    Indexes.compoundIndex(
                            Indexes.ascending("companyName"),
                            Indexes.ascending("source")
                    )
            );
            logger.info("Enrichment cache indexes ensured");
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to create enrichment cache indexes", e);
        }
    }
}
