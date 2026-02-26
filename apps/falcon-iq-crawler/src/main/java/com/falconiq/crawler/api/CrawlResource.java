package com.falconiq.crawler.api;

import com.falconiq.crawler.core.CrawlJob;
import com.falconiq.crawler.core.CrawlManager;
import com.falconiq.crawler.core.CrawlResult;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Path("/crawl")
public class CrawlResource {

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response startCrawl(Map<String, Object> request) {
        String url = (String) request.get("url");
        if (url == null || url.isBlank()) {
            return Response.status(400)
                    .entity(Map.of("error", "url is required"))
                    .build();
        }

        String websiteCrawlDetailId = (String) request.get("websiteCrawlDetailId");
        if (websiteCrawlDetailId == null || websiteCrawlDetailId.isBlank()) {
            return Response.status(400)
                    .entity(Map.of("error", "websiteCrawlDetailId is required"))
                    .build();
        }

        int maxPages = getInt(request, "maxPages", 100);
        int threads = getInt(request, "threads", 5);
        long delayMs = getLong(request, "delayMs", 1000);

        maxPages = Math.min(maxPages, 1000);

        CrawlManager manager = CrawlManager.getInstance();
        CrawlJob job;
        try {
            job = manager.startCrawl(url, maxPages, threads, delayMs, websiteCrawlDetailId);
        } catch (IllegalStateException e) {
            return Response.status(429)
                    .entity(Map.of("error", e.getMessage()))
                    .build();
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("crawlId", job.getId());
        response.put("status", job.getStatus());
        response.put("message", "Crawl started");

        return Response.status(202).entity(response).build();
    }

    @GET
    @Path("/{id}/status")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getCrawlStatus(@PathParam("id") String crawlId) {
        CrawlManager manager = CrawlManager.getInstance();
        CrawlJob job = manager.getJob(crawlId);

        if (job == null) {
            return Response.status(404)
                    .entity(Map.of("error", "Crawl not found: " + crawlId))
                    .build();
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("crawlId", job.getId());
        response.put("status", job.getStatus());
        response.put("url", job.getUrl());
        response.put("pagesDownloaded", job.getPagesDownloaded());
        response.put("maxPages", job.getMaxPages());
        response.put("startedAt", job.getStartedAt());

        if (job.getCompletedAt() != null) {
            response.put("completedAt", job.getCompletedAt());
        }
        if (job.getError() != null) {
            response.put("error", job.getError());
        }
        if ("COMPLETED".equals(job.getStatus())) {
            List<Map<String, Object>> results = job.getResults().stream()
                    .map(r -> {
                        Map<String, Object> m = new LinkedHashMap<>();
                        m.put("url", r.url());
                        m.put("storagePath", r.storagePath());
                        m.put("statusCode", r.statusCode());
                        return m;
                    })
                    .toList();
            response.put("results", results);
        }

        return Response.ok(response).build();
    }

    private static int getInt(Map<String, Object> map, String key, int defaultValue) {
        Object val = map.get(key);
        if (val instanceof Number n) return n.intValue();
        if (val instanceof String s) return Integer.parseInt(s);
        return defaultValue;
    }

    private static long getLong(Map<String, Object> map, String key, long defaultValue) {
        Object val = map.get(key);
        if (val instanceof Number n) return n.longValue();
        if (val instanceof String s) return Long.parseLong(s);
        return defaultValue;
    }
}
