package com.falconiq.crawler.storage;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Stores crawled pages on the local filesystem.
 * Pages are saved under {baseDir}/{crawlId}/{filename}.
 */
public class LocalStorageService implements StorageService {

    private static final Logger logger = Logger.getLogger(LocalStorageService.class.getName());
    private final Path baseDir;

    public LocalStorageService(String outputDir) {
        this.baseDir = Path.of(outputDir);
    }

    @Override
    public String savePage(String crawlId, String url, String html) {
        try {
            Path crawlDir = baseDir.resolve(crawlId);
            Files.createDirectories(crawlDir);
            String filename = generateFilename(url);
            Path filePath = crawlDir.resolve(filename);
            Files.writeString(filePath, html);
            return filePath.toString();
        } catch (IOException e) {
            logger.log(Level.WARNING, "Failed to save page: " + url, e);
            throw new RuntimeException("Failed to save page to local filesystem", e);
        }
    }

    @Override
    public boolean isHealthy() {
        try {
            Files.createDirectories(baseDir);
            return Files.isWritable(baseDir);
        } catch (IOException e) {
            return false;
        }
    }
}
