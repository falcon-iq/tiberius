package com.example.api;

import com.example.domain.objects.BenchmarkRequestEvent;
import com.example.fiq.generic.GenericBeanDescriptorFactory;
import com.example.fiq.generic.GenericBeanType;
import com.example.fiq.generic.GenericMongoCRUDService;

import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.container.ContainerResponseContext;
import jakarta.ws.rs.container.ContainerResponseFilter;
import jakarta.ws.rs.ext.Provider;

import java.io.IOException;
import java.util.logging.Level;
import java.util.logging.Logger;

@Provider
public class BenchmarkTrackingFilter implements ContainerRequestFilter, ContainerResponseFilter {

    private static final Logger logger = Logger.getLogger(BenchmarkTrackingFilter.class.getName());
    private static final String START_TIME_PROPERTY = "benchmarkTrackingStartTime";
    private static final String EVENT_TYPE_PROPERTY = "benchmarkTrackingEventType";

    private final GenericMongoCRUDService<BenchmarkRequestEvent> eventService;

    public BenchmarkTrackingFilter() {
        this.eventService = GenericBeanDescriptorFactory.getInstance()
                .getCRUDService(GenericBeanType.BENCHMARK_REQUEST_EVENT);
    }

    @Override
    public void filter(ContainerRequestContext requestContext) throws IOException {
        String path = requestContext.getUriInfo().getPath();
        String method = requestContext.getMethod();

        // Only track POST requests to /start and /suggest-competitors
        BenchmarkRequestEvent.EventType eventType = getEventType(method, path);
        if (eventType == null) {
            return;
        }

        requestContext.setProperty(START_TIME_PROPERTY, System.currentTimeMillis());
        requestContext.setProperty(EVENT_TYPE_PROPERTY, eventType);
    }

    @Override
    public void filter(ContainerRequestContext requestContext, ContainerResponseContext responseContext)
            throws IOException {
        Object eventTypeObj = requestContext.getProperty(EVENT_TYPE_PROPERTY);
        if (eventTypeObj == null) {
            return;
        }

        try {
            BenchmarkRequestEvent.EventType eventType = (BenchmarkRequestEvent.EventType) eventTypeObj;
            long startTime = (Long) requestContext.getProperty(START_TIME_PROPERTY);

            BenchmarkRequestEvent event = new BenchmarkRequestEvent();
            event.setEventType(eventType.name());
            event.setIpAddress(extractClientIp(requestContext));
            event.setUserAgent(requestContext.getHeaderString("User-Agent"));
            event.setReferer(requestContext.getHeaderString("Referer"));
            event.setCountry(requestContext.getHeaderString("CF-IPCountry"));
            event.setResponseStatus(responseContext.getStatus());
            event.setProcessingTimeMs(System.currentTimeMillis() - startTime);

            // Business-level properties set by the resource method
            Object companyUrl = requestContext.getProperty("tracking.companyUrl");
            if (companyUrl != null) {
                event.setCompanyUrl((String) companyUrl);
            }
            Object competitorCount = requestContext.getProperty("tracking.competitorCount");
            if (competitorCount != null) {
                event.setCompetitorCount((Integer) competitorCount);
            }
            Object benchmarkReportId = requestContext.getProperty("tracking.benchmarkReportId");
            if (benchmarkReportId != null) {
                event.setBenchmarkReportId((String) benchmarkReportId);
            }
            Object cacheHit = requestContext.getProperty("tracking.cacheHit");
            if (cacheHit != null) {
                event.setCacheHit((Boolean) cacheHit);
            }
            Object email = requestContext.getProperty("tracking.email");
            if (email != null) {
                event.setEmail((String) email);
            }

            eventService.create(event);
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to save benchmark tracking event", e);
        }
    }

    private BenchmarkRequestEvent.EventType getEventType(String method, String path) {
        if (!"POST".equals(method)) {
            return null;
        }
        if (path.endsWith("company-benchmark-report/start")) {
            return BenchmarkRequestEvent.EventType.BENCHMARK_START;
        }
        if (path.endsWith("company-benchmark-report/suggest-competitors")) {
            return BenchmarkRequestEvent.EventType.SUGGEST_COMPETITORS;
        }
        return null;
    }

    private String extractClientIp(ContainerRequestContext requestContext) {
        // CF-Connecting-IP is set by Cloudflare (if traffic goes through CF)
        String ip = requestContext.getHeaderString("CF-Connecting-IP");
        if (ip != null && !ip.isBlank()) {
            return ip.trim();
        }

        // X-Forwarded-For is set by ALB/proxies — take the leftmost (original client)
        String xForwardedFor = requestContext.getHeaderString("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isBlank()) {
            return xForwardedFor.split(",")[0].trim();
        }

        // X-Real-IP fallback
        String xRealIp = requestContext.getHeaderString("X-Real-IP");
        if (xRealIp != null && !xRealIp.isBlank()) {
            return xRealIp.trim();
        }

        return null;
    }
}
