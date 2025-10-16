package com.example.api;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import com.example.db.MongoClientProvider;
import com.mongodb.client.MongoClient;

import java.util.Map;

@Path("/health")
public class HealthCheckResource {

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response healthCheck() {
        try {
            // Check MongoDB connectivity
            MongoClient client = MongoClientProvider.getInstance().getOrCreateMongoClient();
            
            // Simple ping to verify connection
            client.getDatabase("admin").runCommand(new org.bson.Document("ping", 1));
            
            // If we get here, all checks passed
            return Response.ok(Map.of(
                "status", "UP",
                "timestamp", System.currentTimeMillis(),
                "service", "falcon-iq-rest",
                "version", "1.0.0",
                "checks", Map.of(
                    "mongodb", "UP",
                    "application", "UP"
                )
            )).build();
            
        } catch (Exception e) {
            // Health check failed
            return Response.status(Response.Status.SERVICE_UNAVAILABLE)
                    .entity(Map.of(
                        "status", "DOWN",
                        "timestamp", System.currentTimeMillis(),
                        "service", "falcon-iq-rest",
                        "version", "1.0.0",
                        "error", e.getMessage(),
                        "checks", Map.of(
                            "mongodb", "DOWN",
                            "application", "UP"
                        )
                    )).build();
        }
    }

    @GET
    @Path("/ready")
    @Produces(MediaType.APPLICATION_JSON)
    public Response readinessCheck() {
        // Readiness check - similar to health but can include more detailed checks
        // Used by Kubernetes/ECS to determine if container is ready to receive traffic
        return healthCheck();
    }

    @GET
    @Path("/live")
    @Produces(MediaType.APPLICATION_JSON)
    public Response livenessCheck() {
        // Liveness check - simpler check to determine if container should be restarted
        return Response.ok(Map.of(
            "status", "UP",
            "timestamp", System.currentTimeMillis()
        )).build();
    }
}