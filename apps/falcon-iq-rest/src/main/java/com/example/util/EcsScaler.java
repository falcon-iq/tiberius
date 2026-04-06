package com.example.util;

import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.ecs.EcsClient;
import software.amazon.awssdk.services.ecs.model.DescribeServicesRequest;
import software.amazon.awssdk.services.ecs.model.DescribeServicesResponse;
import software.amazon.awssdk.services.ecs.model.Service;
import software.amazon.awssdk.services.ecs.model.UpdateServiceRequest;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Scales ECS services up/down on demand.
 * Used to start crawler + analyzer before benchmarks and stop them after.
 */
public class EcsScaler {

    private static final Logger logger = Logger.getLogger(EcsScaler.class.getName());

    private static final String CLUSTER = System.getenv("ECS_CLUSTER_NAME");
    private static final String CRAWLER_SERVICE = System.getenv("ECS_CRAWLER_SERVICE");
    private static final String ANALYZER_SERVICE = System.getenv("ECS_ANALYZER_SERVICE");
    private static final String AWS_REGION = System.getenv("AWS_REGION");

    private static final int POLL_INTERVAL_MS = 5000;
    private static final int MAX_WAIT_MS = 180_000; // 3 minutes

    private static EcsClient client;

    private static EcsClient getClient() {
        if (client == null && AWS_REGION != null) {
            client = EcsClient.builder()
                    .region(Region.of(AWS_REGION))
                    .build();
        }
        return client;
    }

    /**
     * Returns true if ECS scaling is configured (env vars set).
     */
    public static boolean isConfigured() {
        return CLUSTER != null && !CLUSTER.isBlank()
                && CRAWLER_SERVICE != null && !CRAWLER_SERVICE.isBlank()
                && ANALYZER_SERVICE != null && !ANALYZER_SERVICE.isBlank()
                && AWS_REGION != null && !AWS_REGION.isBlank();
    }

    /**
     * Ensure crawler and analyzer are running (desired_count >= 1).
     * If already running, returns immediately. Otherwise scales up and waits.
     */
    public static void ensureServicesRunning() {
        if (!isConfigured()) {
            logger.fine("ECS scaling not configured — skipping");
            return;
        }

        try {
            resetScaleDownFlag();
            boolean crawlerUp = ensureServiceRunning(CRAWLER_SERVICE);
            boolean analyzerUp = ensureServiceRunning(ANALYZER_SERVICE);

            if (!crawlerUp || !analyzerUp) {
                // Wait for services to become healthy
                logger.info("Waiting for services to start...");
                waitForService(CRAWLER_SERVICE);
                waitForService(ANALYZER_SERVICE);
            }
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to scale ECS services", e);
        }
    }

    private static volatile boolean scaleDownTriggered = false;

    /**
     * Scale crawler and analyzer back to 0. Only executes once per scale-up cycle.
     * Safe to call multiple times (e.g. from polling endpoint).
     */
    public static void scaleDownIfRunning() {
        if (!isConfigured() || scaleDownTriggered) return;

        try {
            EcsClient ecs = getClient();
            if (ecs == null) return;

            // Check if services are actually running before scaling down
            DescribeServicesResponse resp = ecs.describeServices(
                    DescribeServicesRequest.builder()
                            .cluster(CLUSTER)
                            .services(CRAWLER_SERVICE, ANALYZER_SERVICE)
                            .build());

            boolean anyRunning = resp.services().stream()
                    .anyMatch(s -> s.desiredCount() > 0);

            if (anyRunning) {
                scaleService(CRAWLER_SERVICE, 0);
                scaleService(ANALYZER_SERVICE, 0);
                scaleDownTriggered = true;
                logger.info("Scaled crawler + analyzer to 0");
            }
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to scale down ECS services", e);
        }
    }

    /**
     * Reset the scale-down flag (called when scaling up).
     */
    private static void resetScaleDownFlag() {
        scaleDownTriggered = false;
    }

    private static boolean ensureServiceRunning(String serviceName) {
        EcsClient ecs = getClient();
        if (ecs == null) return true;

        DescribeServicesResponse resp = ecs.describeServices(
                DescribeServicesRequest.builder()
                        .cluster(CLUSTER)
                        .services(serviceName)
                        .build());

        if (resp.services().isEmpty()) {
            logger.warning("ECS service not found: " + serviceName);
            return true;
        }

        Service svc = resp.services().get(0);
        if (svc.runningCount() > 0) {
            logger.fine(serviceName + " already running (" + svc.runningCount() + " tasks)");
            return true;
        }

        // Scale up to 1
        logger.info("Scaling up " + serviceName + " to 1 task");
        scaleService(serviceName, 1);
        return false;
    }

    private static void scaleService(String serviceName, int desiredCount) {
        EcsClient ecs = getClient();
        if (ecs == null) return;

        ecs.updateService(UpdateServiceRequest.builder()
                .cluster(CLUSTER)
                .service(serviceName)
                .desiredCount(desiredCount)
                .build());
    }

    private static void waitForService(String serviceName) {
        EcsClient ecs = getClient();
        if (ecs == null) return;

        long deadline = System.currentTimeMillis() + MAX_WAIT_MS;
        while (System.currentTimeMillis() < deadline) {
            DescribeServicesResponse resp = ecs.describeServices(
                    DescribeServicesRequest.builder()
                            .cluster(CLUSTER)
                            .services(serviceName)
                            .build());

            if (!resp.services().isEmpty()) {
                Service svc = resp.services().get(0);
                if (svc.runningCount() > 0) {
                    logger.info(serviceName + " is running (" + svc.runningCount() + " tasks)");
                    return;
                }
            }

            try {
                Thread.sleep(POLL_INTERVAL_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
        }
        logger.warning(serviceName + " did not start within timeout");
    }
}
