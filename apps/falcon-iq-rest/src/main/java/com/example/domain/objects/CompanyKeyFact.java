package com.example.domain.objects;

public class CompanyKeyFact {
    private String label;
    private String value;
    private String source;
    private String sourceUrl;

    public CompanyKeyFact() {}

    public CompanyKeyFact(String label, String value, String source, String sourceUrl) {
        this.label = label;
        this.value = value;
        this.source = source;
        this.sourceUrl = sourceUrl;
    }

    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public String getValue() { return value; }
    public void setValue(String value) { this.value = value; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public String getSourceUrl() { return sourceUrl; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }
}
