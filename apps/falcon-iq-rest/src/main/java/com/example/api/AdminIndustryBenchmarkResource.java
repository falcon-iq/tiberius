package com.example.api;

import com.example.api.filters.AdminOnly;
import com.example.domain.objects.IndustryBenchmark;
import com.example.domain.objects.IndustryBenchmarkConfig;
import com.example.domain.objects.IndustryCompanyConfig;
import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericMongoCRUDService;
import com.example.fiq.generic.Filter;
import com.example.fiq.generic.FilterOperator;
import com.example.util.UrlUtils;
import com.example.util.CrawlDetailLookup;
import com.example.db.MongoClientProvider;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mongodb.client.MongoClient;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Updates;
import org.bson.Document;
import org.bson.types.ObjectId;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
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

@Path("/admin/industry-benchmarks")
@AdminOnly
public class AdminIndustryBenchmarkResource {

    private static final Logger logger = Logger.getLogger(AdminIndustryBenchmarkResource.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final String OPENAI_API_URL = "https://api.openai.com/v1/chat/completions";
    private static final String CRAWLER_API_URL = System.getenv("CRAWLER_API_URL");
    private static final String ANALYZER_API_URL = System.getenv("ANALYZER_API_URL");

    private final GenericMongoCRUDService<IndustryBenchmarkConfig> configService;
    private final GenericMongoCRUDService<IndustryBenchmark> benchmarkService;
    private final GenericMongoCRUDService<WebsiteCrawlDetail> crawlDetailService;

    public AdminIndustryBenchmarkResource() {
        this.configService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.INDUSTRY_BENCHMARK_CONFIG);
        this.benchmarkService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.INDUSTRY_BENCHMARK);
        this.crawlDetailService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.WEBSITE_CRAWL_DETAIL);
    }

    @POST
    @Path("/generate-config")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response generateConfig(Map<String, Object> request) {
        String industryName = (String) request.get("industryName");
        String country = (String) request.get("country");

        if (industryName == null || industryName.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "industryName is required")).build();
        }
        if (country == null || country.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "country is required")).build();
        }

        String slug = generateSlug(industryName, country);

        // Check if config already exists
        List<Filter> filters = List.of(new Filter("slug", FilterOperator.EQUALS, List.of(slug)));
        List<IndustryBenchmarkConfig> existing = configService.list(filters, null, null, null);
        if (!existing.isEmpty()) {
            return Response.ok(existing.get(0)).build();
        }

        try {
            List<IndustryCompanyConfig> companies = suggestCompaniesViaLlm(industryName, country);

            IndustryBenchmarkConfig config = new IndustryBenchmarkConfig();
            config.setIndustryName(industryName);
            config.setCountry(country);
            config.setSlug(slug);
            config.setStatus(IndustryBenchmarkConfig.Status.DRAFT);
            config.setCompanies(companies);

            IndustryBenchmarkConfig saved = configService.create(config);
            return Response.status(Response.Status.CREATED).entity(saved).build();

        } catch (Exception e) {
            logger.log(Level.SEVERE, "Failed to generate config for " + industryName, e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(Map.of("error", "Failed to generate config: " + e.getMessage())).build();
        }
    }

    @GET
    @Path("/configs")
    @Produces(MediaType.APPLICATION_JSON)
    public Response listConfigs() {
        List<IndustryBenchmarkConfig> configs = configService.list(null, null, null, null);
        return Response.ok(configs).build();
    }

    @GET
    @Path("/configs/{slug}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getConfig(@PathParam("slug") String slug) {
        List<Filter> filters = List.of(new Filter("slug", FilterOperator.EQUALS, List.of(slug)));
        List<IndustryBenchmarkConfig> configs = configService.list(filters, null, null, null);
        if (configs.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "Config not found")).build();
        }
        return Response.ok(configs.get(0)).build();
    }

    @PUT
    @Path("/configs/{slug}")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    @SuppressWarnings("unchecked")
    public Response updateConfig(@PathParam("slug") String slug, Map<String, Object> request) {
        List<Filter> filters = List.of(new Filter("slug", FilterOperator.EQUALS, List.of(slug)));
        List<IndustryBenchmarkConfig> configs = configService.list(filters, null, null, null);
        if (configs.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "Config not found")).build();
        }

        IndustryBenchmarkConfig config = configs.get(0);

        Object companiesObj = request.get("companies");
        if (companiesObj instanceof List) {
            List<Map<String, String>> companiesMaps = (List<Map<String, String>>) companiesObj;
            List<IndustryCompanyConfig> companies = new ArrayList<>();
            for (Map<String, String> compMap : companiesMaps) {
                companies.add(new IndustryCompanyConfig(compMap.get("name"), compMap.get("url")));
            }
            config.setCompanies(companies);
        }

        // Update directly via MongoDB — convert to Documents for BSON serialization
        List<Document> companyDocs = new ArrayList<>();
        for (IndustryCompanyConfig c : config.getCompanies()) {
            companyDocs.add(new Document("name", c.getName()).append("url", c.getUrl()));
        }
        updateConfigField(config.getId(), "companies", companyDocs);
        return Response.ok(config).build();
    }

    @POST
    @Path("/{slug}/reset")
    @Produces(MediaType.APPLICATION_JSON)
    public Response resetConfig(@PathParam("slug") String slug) {
        List<Filter> filters = List.of(new Filter("slug", FilterOperator.EQUALS, List.of(slug)));
        List<IndustryBenchmarkConfig> configs = configService.list(filters, null, null, null);
        if (configs.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "Config not found")).build();
        }

        IndustryBenchmarkConfig config = configs.get(0);
        updateConfigField(config.getId(), "status", "DRAFT");

        // Also delete the old benchmark result so it regenerates
        MongoClient mongoClient = MongoClientProvider.getInstance().getOrCreateMongoClient();
        mongoClient.getDatabase("company_db").getCollection("industry_benchmark")
                .deleteMany(Filters.eq("slug", slug));

        return Response.ok(Map.of("status", "DRAFT", "slug", slug, "message", "Config reset to DRAFT, old benchmark deleted")).build();
    }

    @POST
    @Path("/{slug}/generate")
    @Produces(MediaType.APPLICATION_JSON)
    public Response triggerGeneration(@PathParam("slug") String slug) {
        List<Filter> filters = List.of(new Filter("slug", FilterOperator.EQUALS, List.of(slug)));
        List<IndustryBenchmarkConfig> configs = configService.list(filters, null, null, null);
        if (configs.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "Config not found")).build();
        }

        IndustryBenchmarkConfig config = configs.get(0);
        if (config.getStatus() == IndustryBenchmarkConfig.Status.GENERATING) {
            return Response.status(Response.Status.CONFLICT)
                    .entity(Map.of("error", "Generation already in progress")).build();
        }

        if (config.getCompanies() == null || config.getCompanies().isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "No companies configured")).build();
        }

        // For each company, reuse existing crawl details or create new ones
        List<Map<String, String>> companiesForAnalyzer = new ArrayList<>();
        List<String> errors = new ArrayList<>();
        List<Map<String, String>> companiesNeedingCrawl = new ArrayList<>();

        // Check if previous companyTasks exist with valid crawl details
        MongoClient mongoClient = MongoClientProvider.getInstance().getOrCreateMongoClient();
        Document configDoc = mongoClient.getDatabase("company_db")
                .getCollection("industry_benchmark_config")
                .find(Filters.eq("_id", new ObjectId(config.getId())))
                .first();

        // Build a map of url → crawlDetailId from previous tasks
        Map<String, String> previousCrawlIds = new LinkedHashMap<>();
        if (configDoc != null && configDoc.containsKey("companyTasks")) {
            @SuppressWarnings("unchecked")
            List<Document> prevTasks = (List<Document>) configDoc.get("companyTasks");
            for (Document t : prevTasks) {
                String taskUrl = t.getString("url");
                String taskCrawlId = t.getString("crawlDetailId");
                if (taskUrl != null && taskCrawlId != null) {
                    previousCrawlIds.put(taskUrl, taskCrawlId);
                }
            }
        }

        for (IndustryCompanyConfig company : config.getCompanies()) {
            String url = UrlUtils.sanitizeInputUrl(company.getUrl());
            String crawlDetailId = null;

            // Try to reuse previous crawl detail if it has results or is completed/failed
            String prevId = previousCrawlIds.get(url);
            if (prevId != null) {
                var prevCrawl = crawlDetailService.findById(prevId);
                if (prevCrawl.isPresent()) {
                    var prevStatus = prevCrawl.get().getStatus();
                    if (prevStatus == WebsiteCrawlDetail.Status.COMPLETED
                            || prevStatus == WebsiteCrawlDetail.Status.FAILED) {
                        crawlDetailId = prevId;
                        logger.info("Reusing previous crawl detail " + prevId + " for " + url + " (status: " + prevStatus + ")");
                    }
                }
            }

            // Fall back to cache lookup or create new
            if (crawlDetailId == null) {
                crawlDetailId = findOrCreateCrawlDetail(url);
            }

            Map<String, String> companyData = new LinkedHashMap<>();
            companyData.put("name", company.getName());
            companyData.put("url", url);
            companyData.put("crawlDetailId", crawlDetailId);
            companiesForAnalyzer.add(companyData);

            // Check if this crawl detail needs crawling
            var crawlOpt = crawlDetailService.findById(crawlDetailId);
            if (crawlOpt.isPresent()) {
                var status = crawlOpt.get().getStatus();
                if (status == WebsiteCrawlDetail.Status.NOT_STARTED) {
                    companiesNeedingCrawl.add(companyData);
                }
            }
        }

        // Persist the company-crawlDetail mapping
        List<Document> companyTasks = new ArrayList<>();
        for (Map<String, String> c : companiesForAnalyzer) {
            companyTasks.add(new Document("name", c.get("name"))
                    .append("url", c.get("url"))
                    .append("crawlDetailId", c.get("crawlDetailId")));
        }
        mongoClient.getDatabase("company_db").getCollection("industry_benchmark_config")
                .updateOne(
                        Filters.eq("_id", new ObjectId(config.getId())),
                        Updates.combine(
                                Updates.set("status", "GENERATING"),
                                Updates.set("companyTasks", companyTasks),
                                Updates.set("modifiedAt", System.currentTimeMillis())
                        )
                );

        // Only trigger crawler for companies that actually need crawling
        if (companiesNeedingCrawl.isEmpty()) {
            logger.info("All companies already have crawl data, skipping crawler");
        } else if (CRAWLER_API_URL == null || CRAWLER_API_URL.isBlank()) {
            errors.add("CRAWLER_API_URL not configured — crawling skipped");
        } else {
            logger.info("Triggering crawl for " + companiesNeedingCrawl.size() + " of " + companiesForAnalyzer.size() + " companies");
            for (Map<String, String> company : companiesNeedingCrawl) {
                int status = -1;
                for (int attempt = 0; attempt < 5; attempt++) {
                    status = triggerCrawl(company.get("url"), company.get("crawlDetailId"));
                    if (status == 429) {
                        long waitMs = (long) Math.pow(2, attempt) * 5000;
                        logger.info("Crawler busy (429), waiting " + waitMs + "ms before retry for " + company.get("url"));
                        try { Thread.sleep(waitMs); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
                    } else {
                        break;
                    }
                }
                if (status != 200 && status != 201 && status != 202) {
                    errors.add("Crawler returned " + status + " for " + company.get("url"));
                }
            }
        }

        // If no companies need crawling, all data is ready — trigger analyzer directly.
        // Otherwise, the analyzer is triggered automatically when the last crawl/analysis
        // completes (via progress_reporter callback in the analyzer service).
        if (companiesNeedingCrawl.isEmpty()) {
            if (ANALYZER_API_URL != null && !ANALYZER_API_URL.isBlank()) {
                int analyzerStatus = triggerAnalyzerPipeline(slug, companiesForAnalyzer);
                if (analyzerStatus != 200 && analyzerStatus != 201 && analyzerStatus != 202) {
                    errors.add("Analyzer returned " + analyzerStatus);
                }
            } else {
                errors.add("ANALYZER_API_URL not configured — analysis skipped");
            }
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("status", errors.isEmpty() ? "IN_PROGRESS" : "IN_PROGRESS_WITH_WARNINGS");
        result.put("slug", slug);
        result.put("companyCount", config.getCompanies().size());
        result.put("companies", companiesForAnalyzer);
        if (!errors.isEmpty()) {
            result.put("warnings", errors);
        }
        return Response.accepted(result).build();
    }

    @GET
    @Path("/{slug}/status")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getStatus(@PathParam("slug") String slug) {
        // Load config
        List<Filter> filters = List.of(new Filter("slug", FilterOperator.EQUALS, List.of(slug)));
        List<IndustryBenchmarkConfig> configs = configService.list(filters, null, null, null);
        if (configs.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "Config not found")).build();
        }

        IndustryBenchmarkConfig config = configs.get(0);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("slug", slug);
        result.put("configStatus", config.getStatus() != null ? config.getStatus().name() : null);
        result.put("industryName", config.getIndustryName());
        result.put("country", config.getCountry());

        // Load companyTasks from MongoDB (raw document, since it's not on the POJO)
        MongoClient mongoClient = MongoClientProvider.getInstance().getOrCreateMongoClient();
        Document configDoc = mongoClient.getDatabase("company_db")
                .getCollection("industry_benchmark_config")
                .find(Filters.eq("_id", new ObjectId(config.getId())))
                .first();

        // Per-company crawl status
        List<Map<String, Object>> companyStatuses = new ArrayList<>();
        if (configDoc != null && configDoc.containsKey("companyTasks")) {
            @SuppressWarnings("unchecked")
            List<Document> tasks = (List<Document>) configDoc.get("companyTasks");
            for (Document task : tasks) {
                Map<String, Object> companyStatus = new LinkedHashMap<>();
                companyStatus.put("name", task.getString("name"));
                companyStatus.put("url", task.getString("url"));
                String crawlDetailId = task.getString("crawlDetailId");
                companyStatus.put("crawlDetailId", crawlDetailId);

                if (crawlDetailId != null && !crawlDetailId.isBlank()) {
                    crawlDetailService.findById(crawlDetailId).ifPresentOrElse(crawl -> {
                        companyStatus.put("crawlStatus", crawl.getStatus() != null ? crawl.getStatus().name() : "UNKNOWN");
                        companyStatus.put("pagesCrawled", crawl.getNumberOfPagesCrawled());
                        companyStatus.put("pagesAnalyzed", crawl.getNumberOfPagesAnalyzed());
                        companyStatus.put("hasAnalysisResults", crawl.getAnalysisResultsPath() != null && !crawl.getAnalysisResultsPath().isBlank());
                        if (crawl.getErrorMessage() != null && !crawl.getErrorMessage().isBlank()) {
                            companyStatus.put("error", crawl.getErrorMessage());
                        }
                    }, () -> {
                        companyStatus.put("crawlStatus", "NOT_FOUND");
                    });
                } else {
                    companyStatus.put("crawlStatus", "NO_CRAWL_DETAIL");
                }

                companyStatuses.add(companyStatus);
            }
        }
        result.put("companies", companyStatuses);

        // Facts sources (per-company: wikidata, llm, wikidata+llm, none)
        if (configDoc != null && configDoc.containsKey("factsSources")) {
            result.put("factsSources", configDoc.get("factsSources"));
        }

        // Environment check
        Map<String, Object> env = new LinkedHashMap<>();
        env.put("crawlerConfigured", CRAWLER_API_URL != null && !CRAWLER_API_URL.isBlank());
        env.put("analyzerConfigured", ANALYZER_API_URL != null && !ANALYZER_API_URL.isBlank());
        if (CRAWLER_API_URL != null) env.put("crawlerUrl", CRAWLER_API_URL);
        if (ANALYZER_API_URL != null) env.put("analyzerUrl", ANALYZER_API_URL);
        result.put("environment", env);

        // Check if benchmark result exists
        List<Filter> benchFilters = List.of(new Filter("slug", FilterOperator.EQUALS, List.of(slug)));
        List<IndustryBenchmark> benchmarks = benchmarkService.list(benchFilters, null, null, null);
        if (!benchmarks.isEmpty()) {
            IndustryBenchmark benchmark = benchmarks.get(0);
            Map<String, Object> benchmarkInfo = new LinkedHashMap<>();
            benchmarkInfo.put("status", benchmark.getStatus() != null ? benchmark.getStatus().name() : null);
            benchmarkInfo.put("generatedAt", benchmark.getGeneratedAt());
            benchmarkInfo.put("companyCount", benchmark.getCompanies() != null ? benchmark.getCompanies().size() : 0);
            if (benchmark.getErrorMessage() != null) {
                benchmarkInfo.put("errorMessage", benchmark.getErrorMessage());
            }
            result.put("benchmark", benchmarkInfo);
        } else {
            result.put("benchmark", null);
        }

        return Response.ok(result).build();
    }

    private String generateSlug(String industryName, String country) {
        String combined = industryName + " " + country;
        return combined.toLowerCase()
                .replaceAll("[^a-z0-9\\s-]", "")
                .replaceAll("\\s+", "-")
                .replaceAll("-+", "-")
                .replaceAll("^-|-$", "");
    }

    private List<IndustryCompanyConfig> suggestCompaniesViaLlm(String industryName, String country) throws Exception {
        String apiKey = System.getenv("OPENAI_API_KEY");
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalStateException("OPENAI_API_KEY environment variable is not configured");
        }

        String systemPrompt = "You are a market research assistant. Given an industry and country, "
                + "list the top 7 most notable companies in that industry in that country. "
                + "Return a JSON object: {\"companies\": [{\"name\": \"Company Name\", \"url\": \"https://company.com\"}, ...]}. "
                + "Return only the JSON, no other text.";

        String userPrompt = String.format("Industry: %s\nCountry: %s", industryName, country);

        Map<String, Object> requestMap = Map.of(
                "model", "gpt-4o-mini",
                "temperature", 0.3,
                "messages", List.of(
                        Map.of("role", "system", "content", systemPrompt),
                        Map.of("role", "user", "content", userPrompt)
                )
        );

        String requestBody = mapper.writeValueAsString(requestMap);

        HttpClient httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(OPENAI_API_URL))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .timeout(Duration.ofSeconds(30))
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .build();

        HttpResponse<String> response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("OpenAI API error: HTTP " + response.statusCode());
        }

        JsonNode root = mapper.readTree(response.body());
        String content = root.at("/choices/0/message/content").asText();
        JsonNode parsed = mapper.readTree(content);
        JsonNode companiesNode = parsed.get("companies");

        List<IndustryCompanyConfig> companies = new ArrayList<>();
        if (companiesNode != null && companiesNode.isArray()) {
            for (JsonNode node : companiesNode) {
                String name = node.has("name") ? node.get("name").asText() : "";
                String url = node.has("url") ? node.get("url").asText() : "";
                if (!name.isBlank() && !url.isBlank()) {
                    companies.add(new IndustryCompanyConfig(name, UrlUtils.sanitizeInputUrl(url)));
                }
            }
        }

        return companies;
    }

    private String findOrCreateCrawlDetail(String url) {
        WebsiteCrawlDetail existing = CrawlDetailLookup.findCompletedCrawl(crawlDetailService, url);
        if (existing != null) {
            logger.info("Reusing crawl detail " + existing.getId() + " for " + url);
            return existing.getId();
        }

        WebsiteCrawlDetail detail = new WebsiteCrawlDetail();
        detail.setWebsiteLink(url);
        detail.setUserId("admin");
        detail.setIsCompetitor(false);
        detail.setStatus(WebsiteCrawlDetail.Status.NOT_STARTED);
        detail.setNumberOfPagesCrawled(0L);
        detail.setNumberOfPagesAnalyzed(0L);

        return crawlDetailService.create(detail).getId();
    }

    private int triggerCrawl(String url, String crawlDetailId) {
        try {
            HttpClient httpClient = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            String body = mapper.writeValueAsString(Map.of(
                    "websiteCrawlDetailId", crawlDetailId,
                    "url", url
            ));

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(CRAWLER_API_URL + "/api/crawl"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(15))
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            logger.info("Crawler response for " + url + ": " + response.statusCode());
            return response.statusCode();
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to trigger crawl for " + url, e);
            return -1;
        }
    }

    private int triggerAnalyzerPipeline(String slug, List<Map<String, String>> companies) {
        try {
            HttpClient httpClient = HttpClient.newBuilder()
                    .version(HttpClient.Version.HTTP_1_1)
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            List<Map<String, String>> companiesPayload = new ArrayList<>();
            for (Map<String, String> company : companies) {
                Map<String, String> entry = new LinkedHashMap<>();
                entry.put("name", company.getOrDefault("name", ""));
                entry.put("url", company.getOrDefault("url", ""));
                entry.put("crawlDetailId", company.getOrDefault("crawlDetailId", ""));
                companiesPayload.add(entry);
            }

            String body = mapper.writeValueAsString(Map.of(
                    "slug", slug,
                    "companies", companiesPayload
            ));

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(ANALYZER_API_URL + "/industry-benchmark"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(15))
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200 && response.statusCode() != 201 && response.statusCode() != 202) {
                logger.warning("Analyzer industry benchmark error " + response.statusCode() + ": " + response.body());
                logger.warning("Request body was: " + body);
            } else {
                logger.info("Analyzer industry benchmark response: " + response.statusCode());
            }
            return response.statusCode();
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to trigger analyzer pipeline for " + slug, e);
            return -1;
        }
    }

    private void updateConfigField(String id, String field, Object value) {
        MongoClient client = MongoClientProvider.getInstance().getOrCreateMongoClient();
        client.getDatabase("company_db").getCollection("industry_benchmark_config")
                .updateOne(
                        Filters.eq("_id", new ObjectId(id)),
                        Updates.combine(
                                Updates.set(field, value),
                                Updates.set("modifiedAt", System.currentTimeMillis())
                        )
                );
    }

}
