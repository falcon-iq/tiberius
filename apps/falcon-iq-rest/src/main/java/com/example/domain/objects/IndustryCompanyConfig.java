package com.example.domain.objects;

public class IndustryCompanyConfig {
    private String name;
    private String url;

    public IndustryCompanyConfig() {}

    public IndustryCompanyConfig(String name, String url) {
        this.name = name;
        this.url = url;
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }
}
