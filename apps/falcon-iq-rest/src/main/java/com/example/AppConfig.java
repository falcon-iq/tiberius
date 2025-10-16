package com.example;

import org.glassfish.jersey.jackson.JacksonFeature;
import org.glassfish.jersey.server.ResourceConfig;
import org.glassfish.jersey.server.model.Resource;
import org.glassfish.jersey.server.model.ResourceMethod;
import org.glassfish.jersey.server.monitoring.ApplicationEvent;
import org.glassfish.jersey.server.monitoring.ApplicationEventListener;
import org.glassfish.jersey.server.monitoring.RequestEvent;
import org.glassfish.jersey.server.monitoring.RequestEventListener;

import jakarta.ws.rs.core.MediaType;
import java.util.logging.Logger;

public class AppConfig extends ResourceConfig {
  private static final Logger logger = Logger.getLogger(AppConfig.class.getName());

  public AppConfig() {
    // auto-register all @Path resources in this package
    packages("com.example.api");
    
    // Explicitly register Jackson for JSON support
    register(JacksonFeature.class);
    
    // Register an application event listener to print all registered APIs
    register(new ApplicationEventListener() {
      @Override
      public void onEvent(ApplicationEvent event) {
        switch (event.getType()) {
          case INITIALIZATION_APP_FINISHED:
            printRegisteredAPIs(event);
            break;
          default:
            break;
        }
      }

      @Override
      public RequestEventListener onRequest(RequestEvent requestEvent) {
        return null;
      }
    });
  }
  
  private void printRegisteredAPIs(ApplicationEvent event) {
    logger.info("=== REGISTERED APIs ===");
    
    java.util.List<Resource> resources = event.getResourceModel().getResources();
    
    for (Resource resource : resources) {
      String basePath = resource.getPath();
      logger.info("Resource: " + basePath);
      
      for (ResourceMethod method : resource.getAllMethods()) {
        String httpMethod = method.getHttpMethod();
        String fullPath = basePath;
        
        // Get path parameters if any
        if (resource.getPathPattern() != null) {
          fullPath = resource.getPathPattern().getTemplate().getTemplate();
        }
        
        // Get produces/consumes info
        StringBuilder methodInfo = new StringBuilder();
        methodInfo.append("  ").append(httpMethod).append(" ").append(fullPath);
        
        if (!method.getProducedTypes().isEmpty()) {
          methodInfo.append(" -> Produces: ");
          for (MediaType mediaType : method.getProducedTypes()) {
            methodInfo.append(mediaType.toString()).append(" ");
          }
        }
        
        if (!method.getConsumedTypes().isEmpty()) {
          methodInfo.append(" <- Consumes: ");
          for (MediaType mediaType : method.getConsumedTypes()) {
            methodInfo.append(mediaType.toString()).append(" ");
          }
        }
        
        logger.info(methodInfo.toString());
      }
      
      // Print child resources (sub-resources)
      for (Resource childResource : resource.getChildResources()) {
        printChildResource(childResource, basePath, 1);
      }
      
      logger.info("");
    }
    
    logger.info("=== END REGISTERED APIs ===");
  }
  
  private void printChildResource(Resource resource, String parentPath, int depth) {
    String indent = "  ".repeat(depth);
    String fullPath = parentPath + resource.getPath();
    
    logger.info(indent + "Sub-resource: " + fullPath);
    
    for (ResourceMethod method : resource.getAllMethods()) {
      String httpMethod = method.getHttpMethod();
      
      StringBuilder methodInfo = new StringBuilder();
      methodInfo.append(indent).append("  ").append(httpMethod).append(" ").append(fullPath);
      
      if (!method.getProducedTypes().isEmpty()) {
        methodInfo.append(" -> Produces: ");
        for (MediaType mediaType : method.getProducedTypes()) {
          methodInfo.append(mediaType.toString()).append(" ");
        }
      }
      
      if (!method.getConsumedTypes().isEmpty()) {
        methodInfo.append(" <- Consumes: ");
        for (MediaType mediaType : method.getConsumedTypes()) {
          methodInfo.append(mediaType.toString()).append(" ");
        }
      }
      
      logger.info(methodInfo.toString());
    }
    
    // Recursively print child resources
    for (Resource childResource : resource.getChildResources()) {
      printChildResource(childResource, fullPath, depth + 1);
    }
  }
}
