package com.example.domain.objects;

import java.util.List;

public class IndustryBenchmark extends AbstractBaseDomainObject {
    public enum Status {
        IN_PROGRESS, COMPLETED, FAILED
    }

    private String industryName;
    private String country;
    private String slug;
    private Status status;
    private Long generatedAt;
    private List<IndustryCompanyEntry> companies;
    private String errorMessage;

    public String getIndustryName() { return industryName; }
    public void setIndustryName(String industryName) { this.industryName = industryName; }
    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }
    public String getSlug() { return slug; }
    public void setSlug(String slug) { this.slug = slug; }
    public Status getStatus() { return status; }
    public void setStatus(Status status) { this.status = status; }
    public Long getGeneratedAt() { return generatedAt; }
    public void setGeneratedAt(Long generatedAt) { this.generatedAt = generatedAt; }
    public List<IndustryCompanyEntry> getCompanies() { return companies; }
    public void setCompanies(List<IndustryCompanyEntry> companies) { this.companies = companies; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
}
