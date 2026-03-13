package com.example.api;

import com.example.domain.objects.CompanyBenchmarkReport;
import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericMongoCRUDService;
import com.example.util.BenchmarkReportLookup;
import com.example.util.CrawlDetailLookup;
import com.example.util.UrlUtils;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.logging.Level;
import java.util.logging.Logger;

@Path("/company-benchmark-report")
public class CompanyBenchmarkReportResource {

    private static final Logger logger = Logger.getLogger(CompanyBenchmarkReportResource.class.getName());
    private static final String CRAWLER_API_URL = System.getenv("CRAWLER_API_URL");

    private final GenericMongoCRUDService<WebsiteCrawlDetail> crawlDetailService;
    private final GenericMongoCRUDService<CompanyBenchmarkReport> benchmarkReportService;

    public CompanyBenchmarkReportResource() {
        this.crawlDetailService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.WEBSITE_CRAWL_DETAIL);
        this.benchmarkReportService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.COMPANY_BENCHMARK_REPORT);
    }

    @POST
    @Path("/start")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    @SuppressWarnings("unchecked")
    public Response start(Map<String, Object> request) {
        String userId = (String) request.get("userId");
        String companyLink = (String) request.get("companyLink");
        List<String> otherCompanyLinks = (List<String>) request.get("otherCompanyLinks");

        if (userId == null || userId.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "userId is required"))
                    .build();
        }
        if (companyLink == null || companyLink.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "companyLink is required"))
                    .build();
        }

        // Sanitize user-provided URLs
        companyLink = UrlUtils.sanitizeInputUrl(companyLink);
        List<String> sanitizedCompetitorLinks = new ArrayList<>();
        if (otherCompanyLinks != null) {
            for (String link : otherCompanyLinks) {
                if (link != null && !link.isBlank()) {
                    sanitizedCompetitorLinks.add(UrlUtils.sanitizeInputUrl(link));
                }
            }
        }

        // Build normalized fingerprints for cache lookup
        String companyLinkNormalized = UrlUtils.normalizeUrl(companyLink);
        String competitorKey = BenchmarkReportLookup.buildCompetitorKey(sanitizedCompetitorLinks);

        // Check for a cached completed benchmark report
        CompanyBenchmarkReport cachedReport = BenchmarkReportLookup.findCompletedBenchmark(
                benchmarkReportService, companyLinkNormalized, competitorKey);
        if (cachedReport != null) {
            logger.info("Returning cached benchmark report " + cachedReport.getId()
                    + " for " + companyLinkNormalized + " vs [" + competitorKey + "]");
            return Response.status(Response.Status.CREATED).entity(cachedReport).build();
        }

        // Try to reuse a recent completed crawl detail for the main company
        String companyCrawlDetailId = findOrCreateCrawlDetail(companyLink, userId, false);

        // Create or reuse WebsiteCrawlDetail for each competitor
        List<String> competitorIds = new ArrayList<>();
        for (String link : sanitizedCompetitorLinks) {
            competitorIds.add(findOrCreateCrawlDetail(link, userId, true));
        }

        // Create CompanyBenchmarkReport
        CompanyBenchmarkReport report = new CompanyBenchmarkReport();
        report.setUserId(userId);
        report.setCompanyCrawlDetailId(companyCrawlDetailId);
        report.setCompetitionCrawlDetailIds(competitorIds);
        report.setCompanyLinkNormalized(companyLinkNormalized);
        report.setCompetitorLinksNormalized(competitorKey);
        report.setStatus(CompanyBenchmarkReport.Status.NOT_STARTED);

        CompanyBenchmarkReport savedReport = benchmarkReportService.create(report);

        // Trigger the crawler service to process all crawls
        if (CRAWLER_API_URL == null || CRAWLER_API_URL.isBlank()) {
            return Response.status(503)
                    .entity(Map.of("error", "CRAWLER_API_URL not configured"))
                    .build();
        }
        try {
            HttpClient httpClient = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            String crawlerBody = String.format(
                    "{\"companyBenchmarkReportId\":\"%s\"}", savedReport.getId());

            HttpRequest crawlerRequest = HttpRequest.newBuilder()
                    .uri(URI.create(CRAWLER_API_URL + "/api/company-benchmark-report/process"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(15))
                    .POST(HttpRequest.BodyPublishers.ofString(crawlerBody))
                    .build();

            HttpResponse<String> crawlerResponse = httpClient.send(
                    crawlerRequest, HttpResponse.BodyHandlers.ofString());

            if (crawlerResponse.statusCode() == 202) {
                logger.info("Crawler accepted benchmark report " + savedReport.getId());
            } else {
                logger.warning("Crawler returned status " + crawlerResponse.statusCode()
                        + " for benchmark report " + savedReport.getId()
                        + ": " + crawlerResponse.body());
                return Response.status(502)
                        .entity(Map.of(
                                "error", "Crawler service error",
                                "crawlerStatus", crawlerResponse.statusCode(),
                                "crawlerResponse", crawlerResponse.body(),
                                "companyBenchmarkReportId", savedReport.getId()))
                        .build();
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Failed to reach crawler service for benchmark report " + savedReport.getId(), e);
            return Response.status(502)
                    .entity(Map.of(
                            "error", "Failed to reach crawler service: " + e.getMessage(),
                            "companyBenchmarkReportId", savedReport.getId()))
                    .build();
        }

        return Response.status(Response.Status.CREATED).entity(savedReport).build();
    }

    @GET
    @Path("/{id}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getStatus(@PathParam("id") String id) {
        try {
            Optional<CompanyBenchmarkReport> reportOpt = benchmarkReportService.findById(id);
            if (reportOpt.isEmpty()) {
                return Response.status(Response.Status.NOT_FOUND)
                        .entity(Map.of("error", "Report not found"))
                        .build();
            }

            CompanyBenchmarkReport report = reportOpt.get();

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("id", id);
            result.put("status", report.getStatus() != null ? report.getStatus().name() : null);
            result.put("reportUrl", report.getReportUrl());
            result.put("htmlReportUrl", report.getHtmlReportUrl());
            result.put("companyCrawlDetailId", report.getCompanyCrawlDetailId());
            result.put("competitionCrawlDetailIds", report.getCompetitionCrawlDetailIds());

            // Look up website links from crawl details for display
            String mainCrawlId = report.getCompanyCrawlDetailId();
            if (mainCrawlId != null) {
                crawlDetailService.findById(mainCrawlId).ifPresent(mainCrawl -> {
                    result.put("companyLink", mainCrawl.getWebsiteLink());
                    result.put("companyStatus", mainCrawl.getStatus() != null ? mainCrawl.getStatus().name() : null);
                });
            }

            List<String> compIds = report.getCompetitionCrawlDetailIds();
            if (compIds != null) {
                List<Map<String, String>> competitors = new ArrayList<>();
                for (String cid : compIds) {
                    crawlDetailService.findById(cid).ifPresent(compCrawl -> {
                        Map<String, String> comp = new LinkedHashMap<>();
                        comp.put("id", cid);
                        comp.put("websiteLink", compCrawl.getWebsiteLink());
                        comp.put("status", compCrawl.getStatus() != null ? compCrawl.getStatus().name() : null);
                        competitors.add(comp);
                    });
                }
                result.put("competitors", competitors);
            }

            return Response.ok(result).build();

        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "Invalid report ID"))
                    .build();
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Failed to get benchmark report status", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(Map.of("error", e.getMessage()))
                    .build();
        }
    }

    private String findOrCreateCrawlDetail(String link, String userId, boolean isCompetitor) {
        WebsiteCrawlDetail existing = CrawlDetailLookup.findCompletedCrawl(crawlDetailService, link);
        if (existing != null) {
            logger.info("Reusing recent crawl detail " + existing.getId()
                    + " for " + (isCompetitor ? "competitor " : "") + link);
            return existing.getId();
        }

        WebsiteCrawlDetail detail = new WebsiteCrawlDetail();
        detail.setWebsiteLink(link);
        detail.setUserId(userId);
        detail.setIsCompetitor(isCompetitor);
        detail.setStatus(WebsiteCrawlDetail.Status.NOT_STARTED);
        detail.setNumberOfPagesCrawled(0L);
        detail.setNumberOfPagesAnalyzed(0L);

        return crawlDetailService.create(detail).getId();
    }
}
