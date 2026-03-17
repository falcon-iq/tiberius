package com.example.api.filters;

import com.example.db.MongoRepository;

import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.Provider;

import org.bson.Document;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoCollection;
import com.example.db.MongoClientProvider;

import java.io.IOException;
import java.util.logging.Logger;

@Provider
@AdminOnly
public class AdminTokenFilter implements ContainerRequestFilter {

    private static final Logger logger = Logger.getLogger(AdminTokenFilter.class.getName());
    private static final String ADMIN_TOKEN_HEADER = "X-Admin-Token";
    private static final String DATABASE = "company_db";
    private static final String COLLECTION = "admin_config";

    @Override
    public void filter(ContainerRequestContext requestContext) throws IOException {
        String token = requestContext.getHeaderString(ADMIN_TOKEN_HEADER);
        if (token == null || token.isBlank()) {
            requestContext.abortWith(
                Response.status(Response.Status.UNAUTHORIZED)
                    .entity(java.util.Map.of("error", "Missing X-Admin-Token header"))
                    .build()
            );
            return;
        }

        try {
            MongoClient client = MongoClientProvider.getInstance().getOrCreateMongoClient();
            MongoCollection<Document> collection = client.getDatabase(DATABASE).getCollection(COLLECTION);
            Document adminConfig = collection.find(new Document("adminToken", token)).first();

            if (adminConfig == null) {
                requestContext.abortWith(
                    Response.status(Response.Status.UNAUTHORIZED)
                        .entity(java.util.Map.of("error", "Invalid admin token"))
                        .build()
                );
            }
        } catch (Exception e) {
            logger.severe("Failed to validate admin token: " + e.getMessage());
            requestContext.abortWith(
                Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(java.util.Map.of("error", "Failed to validate admin token"))
                    .build()
            );
        }
    }
}
