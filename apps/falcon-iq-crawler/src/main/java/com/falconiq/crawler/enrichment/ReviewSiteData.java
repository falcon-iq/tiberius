package com.falconiq.crawler.enrichment;

/**
 * Rating data extracted from a third-party review site (Capterra, TrustRadius, Trustpilot, etc.).
 */
public class ReviewSiteData {

    private String siteName;   // "capterra", "trustradius", "trustpilot", "getapp", "peerspot"
    private String url;
    private Double rating;
    private int reviewCount;
    private String snippet;    // Short excerpt from the search result

    public ReviewSiteData() {}

    public ReviewSiteData(String siteName, String url, Double rating, int reviewCount, String snippet) {
        this.siteName = siteName;
        this.url = url;
        this.rating = rating;
        this.reviewCount = reviewCount;
        this.snippet = snippet;
    }

    public String getSiteName() { return siteName; }
    public void setSiteName(String siteName) { this.siteName = siteName; }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public Double getRating() { return rating; }
    public void setRating(Double rating) { this.rating = rating; }

    public int getReviewCount() { return reviewCount; }
    public void setReviewCount(int reviewCount) { this.reviewCount = reviewCount; }

    public String getSnippet() { return snippet; }
    public void setSnippet(String snippet) { this.snippet = snippet; }
}
