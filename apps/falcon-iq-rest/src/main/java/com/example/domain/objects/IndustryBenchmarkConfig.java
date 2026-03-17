package com.example.domain.objects;

import java.util.List;

public class IndustryBenchmarkConfig extends AbstractBaseDomainObject {
    public enum Status {
        DRAFT, GENERATING, COMPLETED, FAILED
    }

    private String industryName;
    private String country;
    private String slug;
    private Status status;
    private List<IndustryCompanyConfig> companies;

    public String getIndustryName() { return industryName; }
    public void setIndustryName(String industryName) { this.industryName = industryName; }
    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }
    public String getSlug() { return slug; }
    public void setSlug(String slug) { this.slug = slug; }
    public Status getStatus() { return status; }
    public void setStatus(Status status) { this.status = status; }
    public List<IndustryCompanyConfig> getCompanies() { return companies; }
    public void setCompanies(List<IndustryCompanyConfig> companies) { this.companies = companies; }
}
