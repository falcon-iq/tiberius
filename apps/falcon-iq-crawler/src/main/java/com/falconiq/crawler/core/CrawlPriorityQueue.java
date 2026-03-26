package com.falconiq.crawler.core;

import java.net.URI;
import java.util.Comparator;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.PriorityBlockingQueue;

/**
 * Priority queue for crawl URLs. High-signal pages (pricing, products, features)
 * are crawled first. Category quotas limit how many pages of each type are crawled.
 */
public class CrawlPriorityQueue {

    /** URL categories with their priority (lower = higher priority) and max page quota. */
    private enum Category {
        PRICING(1, 10),
        PRODUCTS(2, 30),
        FEATURES(2, 30),
        SOLUTIONS(3, 20),
        INTEGRATIONS(3, 15),
        CUSTOMERS(4, 15),
        CASE_STUDIES(4, 10),
        SECURITY(5, 10),
        ABOUT(6, 5),
        BLOG(7, 10),
        DOCS(7, 200),
        OTHER(8, Integer.MAX_VALUE);

        final int priority;
        final int quota;

        Category(int priority, int quota) {
            this.priority = priority;
            this.quota = quota;
        }
    }

    private static final Map<String, Category> PATH_CATEGORY_MAP = Map.ofEntries(
            Map.entry("/pricing", Category.PRICING),
            Map.entry("/plans", Category.PRICING),
            Map.entry("/products", Category.PRODUCTS),
            Map.entry("/product", Category.PRODUCTS),
            Map.entry("/features", Category.FEATURES),
            Map.entry("/capabilities", Category.FEATURES),
            Map.entry("/solutions", Category.SOLUTIONS),
            Map.entry("/platform", Category.SOLUTIONS),
            Map.entry("/integrations", Category.INTEGRATIONS),
            Map.entry("/partners", Category.INTEGRATIONS),
            Map.entry("/marketplace", Category.INTEGRATIONS),
            Map.entry("/customers", Category.CUSTOMERS),
            Map.entry("/case-studies", Category.CASE_STUDIES),
            Map.entry("/case-study", Category.CASE_STUDIES),
            Map.entry("/security", Category.SECURITY),
            Map.entry("/compliance", Category.SECURITY),
            Map.entry("/trust", Category.SECURITY),
            Map.entry("/about", Category.ABOUT),
            Map.entry("/company", Category.ABOUT),
            Map.entry("/blog", Category.BLOG),
            Map.entry("/docs", Category.DOCS),
            Map.entry("/documentation", Category.DOCS),
            Map.entry("/help", Category.DOCS)
    );

    /** High-signal paths to seed into the queue from sitemap results. */
    public static final Set<String> HIGH_SIGNAL_PATHS = Set.of(
            "/pricing", "/products", "/features", "/solutions",
            "/integrations", "/customers", "/case-studies",
            "/security", "/platform", "/plans"
    );

    private final PriorityBlockingQueue<PrioritizedUrl> queue;
    private final Map<Category, Integer> categoryCounts = new ConcurrentHashMap<>();

    public CrawlPriorityQueue() {
        this.queue = new PriorityBlockingQueue<>(100,
                Comparator.comparingInt(PrioritizedUrl::priority));
    }

    /**
     * Add a URL to the queue if its category quota isn't exhausted.
     * Returns true if added, false if quota exceeded.
     */
    public boolean offer(String url) {
        Category cat = classify(url);
        int count = categoryCounts.getOrDefault(cat, 0);
        if (count >= cat.quota) {
            return false;
        }
        categoryCounts.merge(cat, 1, Integer::sum);
        queue.add(new PrioritizedUrl(url, cat.priority));
        return true;
    }

    /** Poll the highest-priority URL, or null if empty. */
    public String poll() {
        PrioritizedUrl p = queue.poll();
        return p != null ? p.url() : null;
    }

    public boolean isEmpty() {
        return queue.isEmpty();
    }

    public int size() {
        return queue.size();
    }

    private Category classify(String url) {
        try {
            String path = URI.create(url).getPath();
            if (path == null) path = "/";
            path = path.toLowerCase();

            // Check exact path prefix matches
            for (Map.Entry<String, Category> entry : PATH_CATEGORY_MAP.entrySet()) {
                if (path.startsWith(entry.getKey())) {
                    return entry.getValue();
                }
            }
            return Category.OTHER;
        } catch (Exception e) {
            return Category.OTHER;
        }
    }

    private record PrioritizedUrl(String url, int priority) {}
}
