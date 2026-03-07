package com.example.domain.objects;

import java.util.List;

public class CompanyBenchmarkReport extends AbstractBaseDomainObject {
    public static final String USER_ID = "userId";
    public static final String COMPANY_CRAWL_DETAIL_ID = "companyCrawlDetailId";
    public static final String COMPETITION_CRAWL_DETAIL_IDS = "competitionCrawlDetailIds";
    public static final String REPORT_URL = "reportUrl";
    public static final String STATUS = "status";

    public enum Status {
        NOT_STARTED, CRAWL_IN_PROGRESS, BENCHMARK_REPORT_IN_PROGRESS
    }

    private String userId;

    private String companyCrawlDetailId;

    private List<String> competitionCrawlDetailIds;

    private String reportUrl;

    private Status status;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
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

    public Status getStatus() {
        return status;
    }

    public void setStatus(Status status) {
        this.status = status;
    }
}
