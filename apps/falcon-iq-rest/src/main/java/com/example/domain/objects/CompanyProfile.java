package com.example.domain.objects;

public class CompanyProfile extends AbstractBaseDomainObject {
    public static final String COMPANY_NAME = "companyName";
    public static final String VERTICAL = "vertical";

    private String companyName;

    private String vertical;

    public String getCompanyName() {
        return companyName;
    }

    public void setCompanyName(String companyName) {
        this.companyName = companyName;
    }

    public String getVertical() {
        return vertical;
    }

    public void setVertical(String vertical) {
        this.vertical = vertical;
    }
}
