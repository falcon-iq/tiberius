package com.example.util;

import com.example.domain.objects.CompetitorSuggestion;
import com.example.fiq.generic.Filter;
import com.example.fiq.generic.FilterOperator;
import com.example.fiq.generic.GenericMongoCRUDService;

import java.util.List;

public final class CompetitorSuggestionLookup {

    private static final long CACHE_TTL_MS = Long.parseLong(
            System.getenv().getOrDefault("COMPETITOR_SUGGESTION_CACHE_TTL_DAYS", "1")) * 24 * 60 * 60 * 1000L;

    private CompetitorSuggestionLookup() {
    }

    /**
     * Finds a recently cached competitor suggestion for the given normalized URL
     * within the cache TTL. Returns null if no matching suggestion is found.
     */
    public static CompetitorSuggestion findCachedSuggestion(
            GenericMongoCRUDService<CompetitorSuggestion> service,
            String normalizedUrl) {
        long cutoff = System.currentTimeMillis() - CACHE_TTL_MS;

        List<Filter> filters = List.of(
                new Filter(CompetitorSuggestion.COMPANY_URL_NORMALIZED, FilterOperator.EQUALS, List.of(normalizedUrl)),
                new Filter("modifiedAt", FilterOperator.GREATER_THAN, List.of(cutoff)));

        List<CompetitorSuggestion> results = service.list(filters, null, null, null);
        return results.stream()
                .filter(s -> s.getCompetitors() != null && !s.getCompetitors().isEmpty())
                .findFirst()
                .orElse(null);
    }
}
