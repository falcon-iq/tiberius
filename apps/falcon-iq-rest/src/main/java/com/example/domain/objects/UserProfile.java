package com.example.domain.objects;

public class UserProfile extends AbstractBaseDomainObject {
    public static final String NAME = "name";
    public static final String EMAIL = "email";
    public static final String COMPANY_ID = "companyId";

    private String name;

    private String email;

    private String companyId;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getCompanyId() {
        return companyId;
    }

    public void setCompanyId(String companyId) {
        this.companyId = companyId;
    }
}
