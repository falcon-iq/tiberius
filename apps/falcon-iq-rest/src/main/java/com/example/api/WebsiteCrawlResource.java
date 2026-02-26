package com.example.api;

import com.example.db.MongoClientProvider;
import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericMongoCRUDService;

import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Updates;
import org.bson.types.ObjectId;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

@Path("/website-crawl")
public class WebsiteCrawlResource {

    private static final Logger logger = Logger.getLogger(WebsiteCrawlResource.class.getName());
    private static final String CRAWLER_API_URL = System.getenv("CRAWLER_API_URL") != null
            ? System.getenv("CRAWLER_API_URL")
            : "http://localhost:8080";

    private final GenericMongoCRUDService<WebsiteCrawlDetail> crudService;

    public WebsiteCrawlResource() {
        this.crudService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.WEBSITE_CRAWL_DETAIL);
    }

    @POST
    @Path("/start")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response startCrawl(Map<String, Object> request) {
        // Validate required fields
        String websiteLink = (String) request.get("websiteLink");
        String companyId = (String) request.get("companyId");
        String userId = (String) request.get("userId");
        Object isCompetitorObj = request.get("isCompetitor");

        if (websiteLink == null || websiteLink.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "websiteLink is required"))
                    .build();
        }
        if (companyId == null || companyId.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "companyId is required"))
                    .build();
        }
        if (userId == null || userId.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "userId is required"))
                    .build();
        }

        Boolean isCompetitor = isCompetitorObj instanceof Boolean b ? b : false;
        int maxPages = getInt(request, "maxPages", 100);

        // Create WebsiteCrawlDetail record
        WebsiteCrawlDetail detail = new WebsiteCrawlDetail();
        detail.setWebsiteLink(websiteLink);
        detail.setCompanyId(companyId);
        detail.setUserId(userId);
        detail.setIsCompetitor(isCompetitor);
        detail.setStatus(WebsiteCrawlDetail.Status.NOT_STARTED);
        detail.setNumberOfPagesCrawled(0L);
        detail.setNumberOfPagesAnalyzed(0L);
        detail.setTotalPages((long) maxPages);

        WebsiteCrawlDetail saved = crudService.create(detail);

        // Call crawler service
        try {
            HttpClient httpClient = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            String crawlerBody = String.format(
                    "{\"url\":\"%s\",\"maxPages\":%d,\"websiteCrawlDetailId\":\"%s\"}",
                    websiteLink, maxPages, saved.getId());

            HttpRequest crawlerRequest = HttpRequest.newBuilder()
                    .uri(URI.create(CRAWLER_API_URL + "/api/crawl"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(15))
                    .POST(HttpRequest.BodyPublishers.ofString(crawlerBody))
                    .build();

            HttpResponse<String> crawlerResponse = httpClient.send(
                    crawlerRequest, HttpResponse.BodyHandlers.ofString());

            if (crawlerResponse.statusCode() == 202) {
                // Update status to CRAWL_IN_PROGRESS directly in MongoDB
                long now = System.currentTimeMillis();
                MongoClientProvider.getInstance().getOrCreateMongoClient()
                        .getDatabase("company_db")
                        .getCollection("website_crawl_detail")
                        .updateOne(
                                Filters.eq("_id", new ObjectId(saved.getId())),
                                Updates.combine(
                                        Updates.set("status", WebsiteCrawlDetail.Status.CRAWL_IN_PROGRESS.name()),
                                        Updates.set("modifiedAt", now)));
                saved.setStatus(WebsiteCrawlDetail.Status.CRAWL_IN_PROGRESS);
                saved.setModifiedAt(now);

                return Response.status(Response.Status.CREATED).entity(saved).build();
            } else {
                logger.warning("Crawler returned status " + crawlerResponse.statusCode()
                        + ": " + crawlerResponse.body());
                return Response.status(502)
                        .entity(Map.of(
                                "error", "Crawler service error",
                                "crawlerStatus", crawlerResponse.statusCode(),
                                "crawlerResponse", crawlerResponse.body(),
                                "websiteCrawlDetailId", saved.getId()))
                        .build();
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Failed to reach crawler service", e);
            return Response.status(502)
                    .entity(Map.of(
                            "error", "Failed to reach crawler service: " + e.getMessage(),
                            "websiteCrawlDetailId", saved.getId()))
                    .build();
        }
    }

    private static int getInt(Map<String, Object> map, String key, int defaultValue) {
        Object val = map.get(key);
        if (val instanceof Number n) return n.intValue();
        if (val instanceof String s) {
            try {
                return Integer.parseInt(s);
            } catch (NumberFormatException e) {
                return defaultValue;
            }
        }
        return defaultValue;
    }
}
