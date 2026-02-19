package com.falconiq.crawler.api;

import com.falconiq.crawler.core.CrawlManager;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.Map;

@Path("/health")
public class HealthCheckResource {

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response healthCheck() {
        CrawlManager manager = CrawlManager.getInstance();
        boolean storageHealthy = manager.isStorageHealthy();

        Map<String, Object> health = Map.of(
                "status", storageHealthy ? "UP" : "DOWN",
                "storage", storageHealthy ? "healthy" : "unhealthy",
                "activeCrawls", manager.getActiveCrawlCount()
        );

        return storageHealthy
                ? Response.ok(health).build()
                : Response.status(503).entity(health).build();
    }
}
