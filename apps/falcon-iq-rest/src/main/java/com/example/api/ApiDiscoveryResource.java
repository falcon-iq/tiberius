package com.example.api;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.Application;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import org.glassfish.jersey.server.ResourceConfig;
import org.glassfish.jersey.server.model.Resource;
import org.glassfish.jersey.server.model.ResourceMethod;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Path("/api-discovery")
public class ApiDiscoveryResource {

    @Context
    private Application application;

    @GET
    @Path("/endpoints")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getAllEndpoints() {
        List<Map<String, Object>> endpoints = new ArrayList<>();
        
        if (application instanceof ResourceConfig) {
            ResourceConfig resourceConfig = (ResourceConfig) application;
            
            java.util.Set<Resource> resources = resourceConfig.getResources();
            
            for (Resource resource : resources) {
                String basePath = resource.getPath();
                
                for (ResourceMethod method : resource.getAllMethods()) {
                    Map<String, Object> endpoint = new HashMap<>();
                    
                    String httpMethod = method.getHttpMethod();
                    String fullPath = basePath;
                    
                    // Get path template if available
                    if (resource.getPathPattern() != null) {
                        fullPath = resource.getPathPattern().getTemplate().getTemplate();
                    }
                    
                    endpoint.put("method", httpMethod);
                    endpoint.put("path", fullPath);
                    endpoint.put("resourceClass", resource.getHandlerClasses().isEmpty() ? 
                        "Unknown" : resource.getHandlerClasses().iterator().next().getName());
                    
                    // Get media types
                    List<String> produces = new ArrayList<>();
                    method.getProducedTypes().forEach(mediaType -> 
                        produces.add(mediaType.toString()));
                    endpoint.put("produces", produces);
                    
                    List<String> consumes = new ArrayList<>();
                    method.getConsumedTypes().forEach(mediaType -> 
                        consumes.add(mediaType.toString()));
                    endpoint.put("consumes", consumes);
                    
                    endpoints.add(endpoint);
                }
                
                // Add child resources (sub-resources)
                addChildResources(resource, basePath, endpoints);
            }
        }
        
        Map<String, Object> result = new HashMap<>();
        result.put("totalEndpoints", endpoints.size());
        result.put("endpoints", endpoints);
        result.put("timestamp", System.currentTimeMillis());
        
        return Response.ok(result).build();
    }
    
    private void addChildResources(Resource resource, String parentPath, List<Map<String, Object>> endpoints) {
        for (Resource childResource : resource.getChildResources()) {
            String fullPath = parentPath + childResource.getPath();
            
            for (ResourceMethod method : childResource.getAllMethods()) {
                Map<String, Object> endpoint = new HashMap<>();
                
                String httpMethod = method.getHttpMethod();
                
                endpoint.put("method", httpMethod);
                endpoint.put("path", fullPath);
                endpoint.put("resourceClass", childResource.getHandlerClasses().isEmpty() ? 
                    "Unknown" : childResource.getHandlerClasses().iterator().next().getName());
                
                // Get media types
                List<String> produces = new ArrayList<>();
                method.getProducedTypes().forEach(mediaType -> 
                    produces.add(mediaType.toString()));
                endpoint.put("produces", produces);
                
                List<String> consumes = new ArrayList<>();
                method.getConsumedTypes().forEach(mediaType -> 
                    consumes.add(mediaType.toString()));
                endpoint.put("consumes", consumes);
                
                endpoints.add(endpoint);
            }
            
            // Recursively add child resources
            addChildResources(childResource, fullPath, endpoints);
        }
    }

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String getApiInfo() {
        return "API Discovery Service - Use /api-discovery/endpoints to get all available endpoints in JSON format";
    }
}