package com.example;

import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.ee10.servlet.ServletContextHandler;
import org.eclipse.jetty.ee10.servlet.ServletHolder;
import org.glassfish.jersey.servlet.ServletContainer;

import java.util.logging.Logger;
import java.util.logging.ConsoleHandler;
import java.util.logging.Level;
import java.util.logging.SimpleFormatter;

public class Main {

  public static void main(String[] args) throws Exception {
    // Configure logging
    setupLogging();
    
    int port = Integer.parseInt(System.getProperty("PORT", "8080"));
    Server server = new Server(port);

    // Root context
    ServletContextHandler context = new ServletContextHandler(ServletContextHandler.SESSIONS);
    context.setContextPath("/");

    // Wire Jersey's Servlet into Jetty and point it at our AppConfig
    ServletHolder jersey = new ServletHolder(new ServletContainer(new AppConfig()));
    jersey.setInitOrder(0); // load early
    context.addServlet(jersey, "/api/*");

    server.setHandler(context);

    try {
      server.start();
      
      System.out.println("=================================");
      System.out.println("🚀 Falcon IQ REST Server Started");
      System.out.println("=================================");
      System.out.println("Server running at http://localhost:" + port + "/api/*");
      System.out.println("");
      System.out.println("Available API Discovery Endpoints:");
      System.out.println("  GET /api/api-discovery - API info");
      System.out.println("  GET /api/api-discovery/endpoints - All endpoints (JSON)");
      System.out.println("  GET /api/health - Health check");
      System.out.println("  GET /api/hello - Simple hello endpoint");
      System.out.println("=================================");
      System.out.println("Check the console logs above for detailed API registration info!");
      System.out.println("=================================");
      
      server.join();
    } finally {
      server.stop();
    }
  }
  
  private static void setupLogging() {
    Logger rootLogger = Logger.getLogger("");
    ConsoleHandler consoleHandler = new ConsoleHandler();
    consoleHandler.setLevel(Level.INFO);
    consoleHandler.setFormatter(new SimpleFormatter());
    rootLogger.addHandler(consoleHandler);
    rootLogger.setLevel(Level.INFO);
  }
}
