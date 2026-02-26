package com.falconiq.crawler.storage;

import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.HeadBucketRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.nio.charset.StandardCharsets;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Stores crawled pages in an S3 bucket.
 * Pages are saved under crawls/{crawlId}/{filename}.
 * Uses the default AWS credential chain (IAM role on Fargate, env vars locally).
 */
public class S3StorageService implements StorageService {

    private static final Logger logger = Logger.getLogger(S3StorageService.class.getName());
    private final S3Client s3Client;
    private final String bucketName;

    public S3StorageService(String bucketName, String region) {
        this.bucketName = bucketName;
        this.s3Client = S3Client.builder()
                .region(Region.of(region))
                .build();
    }

    @Override
    public String savePage(String crawlId, String url, String html) {
        String filename = generateFilename(url);
        String key = "crawls/" + crawlId + "/" + filename;

        try {
            PutObjectRequest putRequest = PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key(key)
                    .contentType("text/html; charset=utf-8")
                    .build();

            byte[] bytes = html.getBytes(StandardCharsets.UTF_8);
            s3Client.putObject(putRequest, RequestBody.fromBytes(bytes));
            return "s3://" + bucketName + "/" + key;
        } catch (Exception e) {
            logger.log(Level.WARNING, "Failed to upload page to S3: " + url, e);
            throw new RuntimeException("Failed to save page to S3", e);
        }
    }

    @Override
    public String getBasePath(String crawlId) {
        return "s3://" + bucketName + "/crawls/" + crawlId;
    }

    @Override
    public boolean isHealthy() {
        try {
            s3Client.headBucket(HeadBucketRequest.builder()
                    .bucket(bucketName)
                    .build());
            return true;
        } catch (Exception e) {
            logger.log(Level.WARNING, "S3 health check failed", e);
            return false;
        }
    }
}
