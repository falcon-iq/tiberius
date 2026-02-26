package com.example.domain.objects;

public class WebsiteCrawlDetail extends AbstractBaseDomainObject {
    public static final String COMPANY_ID = "companyId";
    public static final String USER_ID = "userId";
    public static final String WEBSITE_LINK = "websiteLink";
    public static final String IS_COMPETITOR = "isCompetitor";
    public static final String NUMBER_OF_PAGES_CRAWLED = "numberOfPagesCrawled";
    public static final String NUMBER_OF_PAGES_ANALYZED = "numberOfPagesAnalyzed";
    public static final String TOTAL_PAGES = "totalPages";
    public static final String STATUS = "status";
    public static final String ERROR_MESSAGE = "errorMessage";
    public static final String CRAWLED_PAGES_PATH = "crawledPagesPath";

    public enum Status {
        NOT_STARTED, CRAWL_IN_PROGRESS, ANALYZER_IN_PROGRESS, COMPLETED, FAILED
    }

    private String companyId;

    private String userId;

    private String websiteLink;

    private Boolean isCompetitor;

    private Long numberOfPagesCrawled;

    private Long numberOfPagesAnalyzed;

    private Long totalPages;

    private Status status;

    private String errorMessage;

    private String crawledPagesPath;

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

    public String getWebsiteLink() {
        return websiteLink;
    }

    public void setWebsiteLink(String websiteLink) {
        this.websiteLink = websiteLink;
    }

    public Boolean getIsCompetitor() {
        return isCompetitor;
    }

    public void setIsCompetitor(Boolean isCompetitor) {
        this.isCompetitor = isCompetitor;
    }

    public Long getNumberOfPagesCrawled() {
        return numberOfPagesCrawled;
    }

    public void setNumberOfPagesCrawled(Long numberOfPagesCrawled) {
        this.numberOfPagesCrawled = numberOfPagesCrawled;
    }

    public Long getNumberOfPagesAnalyzed() {
        return numberOfPagesAnalyzed;
    }

    public void setNumberOfPagesAnalyzed(Long numberOfPagesAnalyzed) {
        this.numberOfPagesAnalyzed = numberOfPagesAnalyzed;
    }

    public Long getTotalPages() {
        return totalPages;
    }

    public void setTotalPages(Long totalPages) {
        this.totalPages = totalPages;
    }

    public Status getStatus() {
        return status;
    }

    public void setStatus(Status status) {
        this.status = status;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public String getCrawledPagesPath() {
        return crawledPagesPath;
    }

    public void setCrawledPagesPath(String crawledPagesPath) {
        this.crawledPagesPath = crawledPagesPath;
    }
}
