package com.example.domain.objects.metadata;

import com.example.domain.objects.BenchmarkReportTask;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class BenchmarkReportTaskBeanDescriptor implements GenericBeanDescriptor<BenchmarkReportTask> {

    @Override
    public String getMongoCollectionName() {
        return "benchmark_report_task";
    }

    @Override
    public String getMongoDatabaseName() {
        return "company_db";
    }

    @Override
    public Class<BenchmarkReportTask> getDomainObjectClazz() {
        return BenchmarkReportTask.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return new BenchmarkReportTaskMetadata();
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.BENCHMARK_REPORT_TASK;
    }
}
