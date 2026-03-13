package com.example.util;

public final class UrlUtils {

    private UrlUtils() {
    }

    /**
     * Sanitizes user input into a valid crawlable URL.
     * Handles: bare domains, mixed case, trailing slashes, missing protocol.
     * Examples:
     *   "sprinklr.com"           -> "https://sprinklr.com"
     *   "WWW.Sprinklr.COM/"      -> "https://www.sprinklr.com"
     *   "http://sprinklr.com"    -> "http://sprinklr.com"
     *   "  sprinklr.com/  "      -> "https://sprinklr.com"
     */
    public static String sanitizeInputUrl(String url) {
        if (url == null || url.isBlank()) return "";
        String sanitized = url.strip().toLowerCase();
        if (!sanitized.startsWith("http://") && !sanitized.startsWith("https://")) {
            sanitized = "https://" + sanitized;
        }
        if (sanitized.endsWith("/")) {
            sanitized = sanitized.substring(0, sanitized.length() - 1);
        }
        return sanitized;
    }

    /**
     * Normalizes a URL by stripping protocol, www prefix, and trailing slash
     * for consistent domain matching.
     */
    public static String normalizeUrl(String url) {
        if (url == null) return "";
        String normalized = url.strip().toLowerCase();
        if (normalized.startsWith("https://")) {
            normalized = normalized.substring(8);
        } else if (normalized.startsWith("http://")) {
            normalized = normalized.substring(7);
        }
        if (normalized.startsWith("www.")) {
            normalized = normalized.substring(4);
        }
        if (normalized.endsWith("/")) {
            normalized = normalized.substring(0, normalized.length() - 1);
        }
        return normalized;
    }
}
