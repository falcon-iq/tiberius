package com.example.util;

import com.example.domain.objects.CompanyBenchmarkReport;
import com.example.fiq.generic.Filter;
import com.example.fiq.generic.FilterOperator;
import com.example.fiq.generic.GenericMongoCRUDService;

import java.util.List;
import java.util.stream.Collectors;

public final class BenchmarkReportLookup {

    private static final long CACHE_TTL_MS = Long.parseLong(
            System.getenv().getOrDefault("CRAWL_CACHE_TTL_DAYS", "1")) * 24 * 60 * 60 * 1000L;

    private BenchmarkReportLookup() {
    }

    /**
     * Builds a normalized, sorted, comma-joined key from a list of competitor URLs.
     * This ensures order-independent matching: [b.com, a.com] and [a.com, b.com] produce the same key.
     */
    public static String buildCompetitorKey(List<String> urls) {
        if (urls == null || urls.isEmpty()) {
            return "";
        }
        return urls.stream()
                .map(UrlUtils::normalizeUrl)
                .sorted()
                .collect(Collectors.joining(","));
    }

    /**
     * Finds a recently completed benchmark report matching the same company and competitors
     * within the cache TTL. Returns null if no matching report is found.
     */
    public static CompanyBenchmarkReport findCompletedBenchmark(
            GenericMongoCRUDService<CompanyBenchmarkReport> service,
            String companyLinkNormalized,
            String competitorKey) {
        long cutoff = System.currentTimeMillis() - CACHE_TTL_MS;

        List<Filter> filters = List.of(
                new Filter(CompanyBenchmarkReport.STATUS, FilterOperator.EQUALS, List.of("COMPLETED")),
                new Filter(CompanyBenchmarkReport.COMPANY_LINK_NORMALIZED, FilterOperator.EQUALS, List.of(companyLinkNormalized)),
                new Filter(CompanyBenchmarkReport.COMPETITOR_LINKS_NORMALIZED, FilterOperator.EQUALS, List.of(competitorKey)),
                new Filter("modifiedAt", FilterOperator.GREATER_THAN, List.of(cutoff)));

        List<CompanyBenchmarkReport> results = service.list(filters, null, null, null);
        return results.stream()
                .filter(r -> r.getReportUrl() != null && !r.getReportUrl().isBlank())
                .findFirst()
                .orElse(null);
    }
}
