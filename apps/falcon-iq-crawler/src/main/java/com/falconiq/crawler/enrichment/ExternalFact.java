package com.falconiq.crawler.enrichment;

public class ExternalFact {

    private String fact;
    private String source; // "g2", "crunchbase", "google_search", "wikidata"
    private String sourceUrl;

    public ExternalFact() {
        this.sourceUrl = "";
    }

    public ExternalFact(String fact, String source, String sourceUrl) {
        this.fact = fact;
        this.source = source;
        this.sourceUrl = sourceUrl;
    }

    public String getFact() { return fact; }
    public void setFact(String fact) { this.fact = fact; }

    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }

    public String getSourceUrl() { return sourceUrl; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }
}
