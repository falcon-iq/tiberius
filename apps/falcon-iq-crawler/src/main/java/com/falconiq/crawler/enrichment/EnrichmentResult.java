package com.falconiq.crawler.enrichment;

import java.util.List;

public class EnrichmentResult {

    private String companyName;
    private G2Data g2;
    private CrunchbaseData crunchbase;
    private List<GoogleSearchInsight> googleInsights;
    private List<ReviewSiteData> reviewSites;
    private List<ExternalFact> externalFacts;
    private boolean cached;
    private String fetchedAt;

    public EnrichmentResult() {
        this.googleInsights = List.of();
        this.reviewSites = List.of();
        this.externalFacts = List.of();
        this.fetchedAt = "";
    }

    public EnrichmentResult(String companyName) {
        this();
        this.companyName = companyName;
    }

    public String getCompanyName() { return companyName; }
    public void setCompanyName(String companyName) { this.companyName = companyName; }

    public G2Data getG2() { return g2; }
    public void setG2(G2Data g2) { this.g2 = g2; }

    public CrunchbaseData getCrunchbase() { return crunchbase; }
    public void setCrunchbase(CrunchbaseData crunchbase) { this.crunchbase = crunchbase; }

    public List<GoogleSearchInsight> getGoogleInsights() { return googleInsights; }
    public void setGoogleInsights(List<GoogleSearchInsight> googleInsights) { this.googleInsights = googleInsights; }

    public List<ReviewSiteData> getReviewSites() { return reviewSites; }
    public void setReviewSites(List<ReviewSiteData> reviewSites) { this.reviewSites = reviewSites; }

    public List<ExternalFact> getExternalFacts() { return externalFacts; }
    public void setExternalFacts(List<ExternalFact> externalFacts) { this.externalFacts = externalFacts; }

    public boolean isCached() { return cached; }
    public void setCached(boolean cached) { this.cached = cached; }

    public String getFetchedAt() { return fetchedAt; }
    public void setFetchedAt(String fetchedAt) { this.fetchedAt = fetchedAt; }
}
