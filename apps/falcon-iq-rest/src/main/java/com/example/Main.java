package com.example;

import org.eclipse.jetty.ee10.servlet.DefaultServlet;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.ee10.servlet.ServletContextHandler;
import org.eclipse.jetty.ee10.servlet.ServletHolder;
import org.eclipse.jetty.util.resource.ResourceFactory;
import org.glassfish.jersey.servlet.ServletContainer;

import java.net.URL;
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

    // Serve static files (e.g. try-market-pilot.html) from classpath "static/" directory
    URL staticUrl = Main.class.getClassLoader().getResource("static");
    if (staticUrl != null) {
      context.setBaseResource(ResourceFactory.of(context).newResource(staticUrl.toURI()));
      ServletHolder defaultServlet = new ServletHolder("default", DefaultServlet.class);
      defaultServlet.setInitParameter("dirAllowed", "false");
      context.addServlet(defaultServlet, "/");
    }

    server.setHandler(context);

    try {
      server.start();

      System.out.println("=================================");
      System.out.println("  Falcon IQ REST Server Started");
      System.out.println("=================================");
      System.out.println("Server running at http://localhost:" + port);
      System.out.println("");
      System.out.println("Pages:");
      System.out.println("  http://localhost:" + port + "/try-market-pilot.html");
      System.out.println("");
      System.out.println("API Endpoints:");
      System.out.println("  GET  /api/api-discovery/endpoints - All endpoints (JSON)");
      System.out.println("  GET  /api/health - Health check");
      System.out.println("  POST /api/company-benchmark-report/start");
      System.out.println("  GET  /api/company-benchmark-report/{id}");
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
