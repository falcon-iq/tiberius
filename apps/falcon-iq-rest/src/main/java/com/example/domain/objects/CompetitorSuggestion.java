package com.example.domain.objects;

import java.util.List;

public class CompetitorSuggestion extends AbstractBaseDomainObject {
    public static final String COMPANY_URL_NORMALIZED = "companyUrlNormalized";
    public static final String COMPETITORS = "competitors";

    private String companyUrlNormalized;
    private List<String> competitors;

    public String getCompanyUrlNormalized() {
        return companyUrlNormalized;
    }

    public void setCompanyUrlNormalized(String companyUrlNormalized) {
        this.companyUrlNormalized = companyUrlNormalized;
    }

    public List<String> getCompetitors() {
        return competitors;
    }

    public void setCompetitors(List<String> competitors) {
        this.competitors = competitors;
    }
}
