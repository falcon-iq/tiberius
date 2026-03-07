package com.example.api;

import com.example.domain.objects.CompanyBenchmarkReport;
import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericMongoCRUDService;

import com.example.db.MongoClientProvider;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import org.bson.Document;
import org.bson.types.ObjectId;

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

        // Create WebsiteCrawlDetail for the main company
        WebsiteCrawlDetail companyDetail = new WebsiteCrawlDetail();
        companyDetail.setWebsiteLink(companyLink);
        companyDetail.setUserId(userId);
        companyDetail.setIsCompetitor(false);
        companyDetail.setStatus(WebsiteCrawlDetail.Status.NOT_STARTED);
        companyDetail.setNumberOfPagesCrawled(0L);
        companyDetail.setNumberOfPagesAnalyzed(0L);

        WebsiteCrawlDetail savedCompany = crawlDetailService.create(companyDetail);

        // Create WebsiteCrawlDetail for each competitor
        List<String> competitorIds = new ArrayList<>();
        if (otherCompanyLinks != null) {
            for (String link : otherCompanyLinks) {
                if (link != null && !link.isBlank()) {
                    WebsiteCrawlDetail competitorDetail = new WebsiteCrawlDetail();
                    competitorDetail.setWebsiteLink(link);
                    competitorDetail.setUserId(userId);
                    competitorDetail.setIsCompetitor(true);
                    competitorDetail.setStatus(WebsiteCrawlDetail.Status.NOT_STARTED);
                    competitorDetail.setNumberOfPagesCrawled(0L);
                    competitorDetail.setNumberOfPagesAnalyzed(0L);

                    WebsiteCrawlDetail savedCompetitor = crawlDetailService.create(competitorDetail);
                    competitorIds.add(savedCompetitor.getId());
                }
            }
        }

        // Create CompanyBenchmarkReport
        CompanyBenchmarkReport report = new CompanyBenchmarkReport();
        report.setUserId(userId);
        report.setCompanyCrawlDetailId(savedCompany.getId());
        report.setCompetitionCrawlDetailIds(competitorIds);
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
            MongoCollection<Document> reportCol = MongoClientProvider.getInstance()
                    .getOrCreateMongoClient()
                    .getDatabase("company_db")
                    .getCollection("company_benchmark_report");

            Document doc = reportCol.find(Filters.eq("_id", new ObjectId(id))).first();
            if (doc == null) {
                return Response.status(Response.Status.NOT_FOUND)
                        .entity(Map.of("error", "Report not found"))
                        .build();
            }

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("id", id);
            result.put("status", doc.getString("status"));
            result.put("reportUrl", doc.getString("reportUrl"));
            result.put("htmlReportUrl", doc.getString("htmlReportUrl"));
            result.put("errorMessage", doc.getString("errorMessage"));
            result.put("companyCrawlDetailId", doc.getString("companyCrawlDetailId"));
            result.put("competitionCrawlDetailIds", doc.getList("competitionCrawlDetailIds", String.class));

            // Look up website links from crawl details for display
            MongoCollection<Document> crawlCol = MongoClientProvider.getInstance()
                    .getOrCreateMongoClient()
                    .getDatabase("company_db")
                    .getCollection("website_crawl_detail");

            String mainCrawlId = doc.getString("companyCrawlDetailId");
            if (mainCrawlId != null) {
                Document mainCrawl = crawlCol.find(Filters.eq("_id", new ObjectId(mainCrawlId))).first();
                if (mainCrawl != null) {
                    result.put("companyLink", mainCrawl.getString("websiteLink"));
                    result.put("companyStatus", mainCrawl.getString("status"));
                }
            }

            List<String> compIds = doc.getList("competitionCrawlDetailIds", String.class);
            if (compIds != null) {
                List<Map<String, String>> competitors = new ArrayList<>();
                for (String cid : compIds) {
                    Document compCrawl = crawlCol.find(Filters.eq("_id", new ObjectId(cid))).first();
                    if (compCrawl != null) {
                        Map<String, String> comp = new LinkedHashMap<>();
                        comp.put("id", cid);
                        comp.put("websiteLink", compCrawl.getString("websiteLink"));
                        comp.put("status", compCrawl.getString("status"));
                        competitors.add(comp);
                    }
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
}
