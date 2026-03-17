package com.example.domain.objects;

import java.util.List;

public class IndustryCompanyEntry {
    private String companyName;
    private String companyUrl;
    private String logoUrl;
    private List<CompanyKeyFact> keyFacts;
    private List<CompanyStrength> strengths;
    private List<CompanyImprovement> improvements;
    private List<CompanyTestimonial> testimonials;

    public String getCompanyName() { return companyName; }
    public void setCompanyName(String companyName) { this.companyName = companyName; }
    public String getCompanyUrl() { return companyUrl; }
    public void setCompanyUrl(String companyUrl) { this.companyUrl = companyUrl; }
    public String getLogoUrl() { return logoUrl; }
    public void setLogoUrl(String logoUrl) { this.logoUrl = logoUrl; }
    public List<CompanyKeyFact> getKeyFacts() { return keyFacts; }
    public void setKeyFacts(List<CompanyKeyFact> keyFacts) { this.keyFacts = keyFacts; }
    public List<CompanyStrength> getStrengths() { return strengths; }
    public void setStrengths(List<CompanyStrength> strengths) { this.strengths = strengths; }
    public List<CompanyImprovement> getImprovements() { return improvements; }
    public void setImprovements(List<CompanyImprovement> improvements) { this.improvements = improvements; }
    public List<CompanyTestimonial> getTestimonials() { return testimonials; }
    public void setTestimonials(List<CompanyTestimonial> testimonials) { this.testimonials = testimonials; }
}
