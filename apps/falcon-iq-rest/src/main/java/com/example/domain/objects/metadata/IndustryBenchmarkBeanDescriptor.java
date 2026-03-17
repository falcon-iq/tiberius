package com.example.domain.objects.metadata;

import com.example.domain.objects.IndustryBenchmark;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class IndustryBenchmarkBeanDescriptor implements GenericBeanDescriptor<IndustryBenchmark> {
    @Override
    public String getMongoCollectionName() { return "industry_benchmark"; }
    @Override
    public String getMongoDatabaseName() { return "company_db"; }
    @Override
    public Class<IndustryBenchmark> getDomainObjectClazz() { return IndustryBenchmark.class; }
    @Override
    public GenericBeanMetadata getGenericBeanMetadata() { return new IndustryBenchmarkMetadata(); }
    @Override
    public GenericBeanType getType() { return GenericBeanType.INDUSTRY_BENCHMARK; }
}
