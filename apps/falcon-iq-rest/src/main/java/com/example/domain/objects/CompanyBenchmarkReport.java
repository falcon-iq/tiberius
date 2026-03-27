package com.example.domain.objects;

import java.util.List;

public class CompanyBenchmarkReport extends AbstractBaseDomainObject {
    public static final String USER_ID = "userId";
    public static final String COMPANY_CRAWL_DETAIL_ID = "companyCrawlDetailId";
    public static final String COMPETITION_CRAWL_DETAIL_IDS = "competitionCrawlDetailIds";
    public static final String REPORT_URL = "reportUrl";
    public static final String HTML_REPORT_URL = "htmlReportUrl";
    public static final String STATUS = "status";
    public static final String COMPANY_LINK_NORMALIZED = "companyLinkNormalized";
    public static final String COMPETITOR_LINKS_NORMALIZED = "competitorLinksNormalized";
    public static final String COMPANY_NAME = "companyName";

    public enum Status {
        NOT_STARTED,
        CRAWL_IN_PROGRESS,
        CRAWL_COMPLETED,
        ANALYSIS_IN_PROGRESS,
        ANALYSIS_COMPLETED,
        ENRICHMENT_IN_PROGRESS,
        BENCHMARK_REPORT_IN_PROGRESS,
        COMPLETED,
        FAILED
    }

    private String userId;

    private String companyName;

    private String companyCrawlDetailId;

    private List<String> competitionCrawlDetailIds;

    private String reportUrl;

    private String htmlReportUrl;

    private Status status;

    private String companyLinkNormalized;

    private String competitorLinksNormalized;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getCompanyName() {
        return companyName;
    }

    public void setCompanyName(String companyName) {
        this.companyName = companyName;
    }

    public String getCompanyCrawlDetailId() {
        return companyCrawlDetailId;
    }

    public void setCompanyCrawlDetailId(String companyCrawlDetailId) {
        this.companyCrawlDetailId = companyCrawlDetailId;
    }

    public List<String> getCompetitionCrawlDetailIds() {
        return competitionCrawlDetailIds;
    }

    public void setCompetitionCrawlDetailIds(List<String> competitionCrawlDetailIds) {
        this.competitionCrawlDetailIds = competitionCrawlDetailIds;
    }

    public String getReportUrl() {
        return reportUrl;
    }

    public void setReportUrl(String reportUrl) {
        this.reportUrl = reportUrl;
    }

    public String getHtmlReportUrl() {
        return htmlReportUrl;
    }

    public void setHtmlReportUrl(String htmlReportUrl) {
        this.htmlReportUrl = htmlReportUrl;
    }

    public Status getStatus() {
        return status;
    }

    public void setStatus(Status status) {
        this.status = status;
    }

    public String getCompanyLinkNormalized() {
        return companyLinkNormalized;
    }

    public void setCompanyLinkNormalized(String companyLinkNormalized) {
        this.companyLinkNormalized = companyLinkNormalized;
    }

    public String getCompetitorLinksNormalized() {
        return competitorLinksNormalized;
    }

    public void setCompetitorLinksNormalized(String competitorLinksNormalized) {
        this.competitorLinksNormalized = competitorLinksNormalized;
    }
}
