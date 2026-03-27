package com.falconiq.crawler.enrichment;

import java.util.List;

public class CrunchbaseData {

    private String founded;
    private String hq;
    private String employeeCount;
    private String totalFunding;
    private List<String> investors;

    public CrunchbaseData() {
        this.investors = List.of();
    }

    public String getFounded() { return founded; }
    public void setFounded(String founded) { this.founded = founded; }

    public String getHq() { return hq; }
    public void setHq(String hq) { this.hq = hq; }

    public String getEmployeeCount() { return employeeCount; }
    public void setEmployeeCount(String employeeCount) { this.employeeCount = employeeCount; }

    public String getTotalFunding() { return totalFunding; }
    public void setTotalFunding(String totalFunding) { this.totalFunding = totalFunding; }

    public List<String> getInvestors() { return investors; }
    public void setInvestors(List<String> investors) { this.investors = investors; }
}
