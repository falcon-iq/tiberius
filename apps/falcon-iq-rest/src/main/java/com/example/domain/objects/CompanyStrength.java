package com.example.domain.objects;

public class CompanyStrength {
    private String title;
    private String detail;

    public CompanyStrength() {}
    public CompanyStrength(String title, String detail) { this.title = title; this.detail = detail; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getDetail() { return detail; }
    public void setDetail(String detail) { this.detail = detail; }
}
