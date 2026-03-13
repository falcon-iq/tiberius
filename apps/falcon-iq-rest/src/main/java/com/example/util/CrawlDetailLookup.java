package com.example.util;

import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.Filter;
import com.example.fiq.generic.FilterOperator;
import com.example.fiq.generic.GenericMongoCRUDService;

import java.util.List;

public class CrawlDetailLookup {

    private static final long CACHE_TTL_MS = Long.parseLong(
            System.getenv().getOrDefault("CRAWL_CACHE_TTL_DAYS", "1")) * 24 * 60 * 60 * 1000L;

    private CrawlDetailLookup() {
    }

    /**
     * Finds a recently completed WebsiteCrawlDetail for the same domain (within 24 hours).
     * Uses normalized URL matching to handle protocol/www/trailing slash differences.
     * Returns the matching detail if found, null otherwise.
     */
    public static WebsiteCrawlDetail findCompletedCrawl(
            GenericMongoCRUDService<WebsiteCrawlDetail> service,
            String websiteLink) {
        String normalized = UrlUtils.normalizeUrl(websiteLink);
        long cutoff = System.currentTimeMillis() - CACHE_TTL_MS;

        List<Filter> filters = List.of(
                new Filter("status", FilterOperator.EQUALS, List.of("COMPLETED")),
                new Filter("modifiedAt", FilterOperator.GREATER_THAN, List.of(cutoff)));

        List<WebsiteCrawlDetail> results = service.list(filters, null, null, null);
        return results.stream()
                .filter(d -> d.getAnalysisResultsPath() != null && !d.getAnalysisResultsPath().isBlank())
                .filter(d -> UrlUtils.normalizeUrl(d.getWebsiteLink()).equals(normalized))
                .findFirst()
                .orElse(null);
    }
}
