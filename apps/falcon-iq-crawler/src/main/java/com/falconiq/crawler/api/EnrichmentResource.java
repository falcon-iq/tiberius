package com.falconiq.crawler.api;

import com.falconiq.crawler.enrichment.EnrichmentManager;
import com.falconiq.crawler.enrichment.EnrichmentResult;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.Map;

@Path("/enrich")
public class EnrichmentResource {

    private static final ObjectMapper mapper = new ObjectMapper();

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response enrich(Map<String, Object> request) {
        String companyName = (String) request.get("companyName");
        if (companyName == null || companyName.isBlank()) {
            return Response.status(400)
                    .entity(Map.of("error", "companyName is required"))
                    .build();
        }

        String companyUrl = (String) request.getOrDefault("companyUrl", "");

        EnrichmentManager manager = EnrichmentManager.getInstance();
        if (manager == null) {
            return Response.status(503)
                    .entity(Map.of("error", "Enrichment service not initialized"))
                    .build();
        }

        EnrichmentResult result = manager.enrich(companyName, companyUrl);

        try {
            String json = mapper.writeValueAsString(result);
            return Response.ok(json, MediaType.APPLICATION_JSON).build();
        } catch (Exception e) {
            return Response.serverError()
                    .entity(Map.of("error", "Failed to serialize enrichment result"))
                    .build();
        }
    }
}
