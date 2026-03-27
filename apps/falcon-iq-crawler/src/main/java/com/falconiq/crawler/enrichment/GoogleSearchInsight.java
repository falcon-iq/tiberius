package com.falconiq.crawler.enrichment;

public class GoogleSearchInsight {

    private String query;
    private String title;
    private String snippet;
    private String url;
    private String insightType; // "review", "comparison", "complaint", "general"

    public GoogleSearchInsight() {
        this.insightType = "general";
    }

    public GoogleSearchInsight(String query, String title, String snippet, String url, String insightType) {
        this.query = query;
        this.title = title;
        this.snippet = snippet;
        this.url = url;
        this.insightType = insightType;
    }

    public String getQuery() { return query; }
    public void setQuery(String query) { this.query = query; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getSnippet() { return snippet; }
    public void setSnippet(String snippet) { this.snippet = snippet; }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public String getInsightType() { return insightType; }
    public void setInsightType(String insightType) { this.insightType = insightType; }
}
