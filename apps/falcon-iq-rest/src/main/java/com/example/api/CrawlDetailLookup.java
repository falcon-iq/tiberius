package com.example.api;

import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.Filter;
import com.example.fiq.generic.FilterOperator;
import com.example.fiq.generic.GenericMongoCRUDService;

import java.util.List;

public class CrawlDetailLookup {

    private static final long TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000L;

    private CrawlDetailLookup() {
    }

    public static WebsiteCrawlDetail findCompletedCrawl(
            GenericMongoCRUDService<WebsiteCrawlDetail> service,
            String websiteLink) {
        long cutoff = System.currentTimeMillis() - TWENTY_FOUR_HOURS_MS;
        List<Filter> filters = List.of(
                new Filter("websiteLink", FilterOperator.EQUALS, List.of(websiteLink)),
                new Filter("status", FilterOperator.EQUALS, List.of("COMPLETED")),
                new Filter("modifiedAt", FilterOperator.GREATER_THAN, List.of(cutoff)));
        List<WebsiteCrawlDetail> results = service.list(filters, null, null, null);
        return results.stream()
                .filter(d -> d.getAnalysisResultsPath() != null && !d.getAnalysisResultsPath().isBlank())
                .findFirst()
                .orElse(null);
    }
}
