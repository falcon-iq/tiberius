package com.example.domain.objects.metadata;

import com.example.domain.objects.CompanyBenchmarkReport;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class CompanyBenchmarkReportBeanDescriptor implements GenericBeanDescriptor<CompanyBenchmarkReport> {

    @Override
    public String getMongoCollectionName() {
        return "company_benchmark_report";
    }

    @Override
    public String getMongoDatabaseName() {
        return "company_db";
    }

    @Override
    public Class<CompanyBenchmarkReport> getDomainObjectClazz() {
        return CompanyBenchmarkReport.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return new CompanyBenchmarkReportMetadata();
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.COMPANY_BENCHMARK_REPORT;
    }
}
