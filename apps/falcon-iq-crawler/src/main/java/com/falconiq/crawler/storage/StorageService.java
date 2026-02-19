package com.falconiq.crawler.storage;

import java.net.URI;
import java.security.MessageDigest;
import java.util.HexFormat;

/**
 * Abstraction for storing crawled pages. Implementations handle
 * local filesystem or S3 storage.
 */
public interface StorageService {

    /**
     * Save a crawled page and return the storage path.
     *
     * @param crawlId unique identifier for this crawl session
     * @param url     the URL that was crawled
     * @param html    the HTML content
     * @return storage path (local file path or S3 URI)
     */
    String savePage(String crawlId, String url, String html);

    /**
     * Check if the storage backend is accessible and writable.
     */
    boolean isHealthy();

    /**
     * Generate a deterministic filename for a URL using path + SHA-256 hash.
     */
    default String generateFilename(String url) {
        try {
            URI uri = URI.create(url);
            String path = uri.getPath();
            if (path == null || path.equals("/") || path.isEmpty()) {
                path = "index";
            } else {
                path = path.replaceAll("^/|/$", "").replace("/", "_");
            }
            String hash = sha256Short(url);
            String name = path + "_" + hash + ".html";
            if (name.length() > 200) {
                name = name.substring(0, 184) + "_" + hash + ".html";
            }
            return name;
        } catch (Exception e) {
            return sha256Short(url) + ".html";
        }
    }

    private static String sha256Short(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(input.getBytes());
            return HexFormat.of().formatHex(digest).substring(0, 16);
        } catch (Exception e) {
            return String.valueOf(input.hashCode());
        }
    }
}
