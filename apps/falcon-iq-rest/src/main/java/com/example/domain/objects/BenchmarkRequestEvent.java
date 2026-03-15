package com.example.domain.objects;

public class BenchmarkRequestEvent extends AbstractBaseDomainObject {
    public static final String EVENT_TYPE = "eventType";
    public static final String IP_ADDRESS = "ipAddress";
    public static final String USER_AGENT = "userAgent";
    public static final String REFERER = "referer";
    public static final String COMPANY_URL = "companyUrl";
    public static final String COMPETITOR_COUNT = "competitorCount";
    public static final String BENCHMARK_REPORT_ID = "benchmarkReportId";
    public static final String CACHE_HIT = "cacheHit";
    public static final String RESPONSE_STATUS = "responseStatus";
    public static final String PROCESSING_TIME_MS = "processingTimeMs";
    public static final String COUNTRY = "country";
    public static final String EMAIL = "email";

    public enum EventType {
        BENCHMARK_START,
        SUGGEST_COMPETITORS
    }

    private String eventType;
    private String ipAddress;
    private String userAgent;
    private String referer;
    private String companyUrl;
    private Integer competitorCount;
    private String benchmarkReportId;
    private Boolean cacheHit;
    private Integer responseStatus;
    private Long processingTimeMs;
    private String country;
    private String email;

    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public String getIpAddress() {
        return ipAddress;
    }

    public void setIpAddress(String ipAddress) {
        this.ipAddress = ipAddress;
    }

    public String getUserAgent() {
        return userAgent;
    }

    public void setUserAgent(String userAgent) {
        this.userAgent = userAgent;
    }

    public String getReferer() {
        return referer;
    }

    public void setReferer(String referer) {
        this.referer = referer;
    }

    public String getCompanyUrl() {
        return companyUrl;
    }

    public void setCompanyUrl(String companyUrl) {
        this.companyUrl = companyUrl;
    }

    public Integer getCompetitorCount() {
        return competitorCount;
    }

    public void setCompetitorCount(Integer competitorCount) {
        this.competitorCount = competitorCount;
    }

    public String getBenchmarkReportId() {
        return benchmarkReportId;
    }

    public void setBenchmarkReportId(String benchmarkReportId) {
        this.benchmarkReportId = benchmarkReportId;
    }

    public Boolean getCacheHit() {
        return cacheHit;
    }

    public void setCacheHit(Boolean cacheHit) {
        this.cacheHit = cacheHit;
    }

    public Integer getResponseStatus() {
        return responseStatus;
    }

    public void setResponseStatus(Integer responseStatus) {
        this.responseStatus = responseStatus;
    }

    public Long getProcessingTimeMs() {
        return processingTimeMs;
    }

    public void setProcessingTimeMs(Long processingTimeMs) {
        this.processingTimeMs = processingTimeMs;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}
