package com.example.domain.objects;

import java.util.List;

public class BenchmarkReportTask extends AbstractBaseDomainObject {
    public static final String COMPANY_ID = "companyId";
    public static final String USER_ID = "userId";
    public static final String MY_WEBSITE_CRAWL_DETAIL_ID = "myWebsiteCrawlDetailId";
    public static final String MY_COMPETITION_CRAWL_DETAIL_IDS = "myCompetitionCrawlDetailIds";
    public static final String TOTAL_TASKS = "totalTasks";
    public static final String PROGRESS = "progress";
    public static final String REPORT_URL = "reportUrl";

    private String companyId;

    private String userId;

    private String myWebsiteCrawlDetailId;

    private List<String> myCompetitionCrawlDetailIds;

    private Long totalTasks;

    private Long progress;

    private String reportUrl;

    public String getCompanyId() {
        return companyId;
    }

    public void setCompanyId(String companyId) {
        this.companyId = companyId;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getMyWebsiteCrawlDetailId() {
        return myWebsiteCrawlDetailId;
    }

    public void setMyWebsiteCrawlDetailId(String myWebsiteCrawlDetailId) {
        this.myWebsiteCrawlDetailId = myWebsiteCrawlDetailId;
    }

    public List<String> getMyCompetitionCrawlDetailIds() {
        return myCompetitionCrawlDetailIds;
    }

    public void setMyCompetitionCrawlDetailIds(List<String> myCompetitionCrawlDetailIds) {
        this.myCompetitionCrawlDetailIds = myCompetitionCrawlDetailIds;
    }

    public Long getTotalTasks() {
        return totalTasks;
    }

    public void setTotalTasks(Long totalTasks) {
        this.totalTasks = totalTasks;
    }

    public Long getProgress() {
        return progress;
    }

    public void setProgress(Long progress) {
        this.progress = progress;
    }

    public String getReportUrl() {
        return reportUrl;
    }

    public void setReportUrl(String reportUrl) {
        this.reportUrl = reportUrl;
    }
}
