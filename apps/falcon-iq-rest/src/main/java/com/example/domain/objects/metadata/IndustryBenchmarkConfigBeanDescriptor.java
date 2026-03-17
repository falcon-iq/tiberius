package com.example.domain.objects.metadata;

import com.example.domain.objects.IndustryBenchmarkConfig;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class IndustryBenchmarkConfigBeanDescriptor implements GenericBeanDescriptor<IndustryBenchmarkConfig> {
    @Override
    public String getMongoCollectionName() { return "industry_benchmark_config"; }
    @Override
    public String getMongoDatabaseName() { return "company_db"; }
    @Override
    public Class<IndustryBenchmarkConfig> getDomainObjectClazz() { return IndustryBenchmarkConfig.class; }
    @Override
    public GenericBeanMetadata getGenericBeanMetadata() { return new IndustryBenchmarkConfigMetadata(); }
    @Override
    public GenericBeanType getType() { return GenericBeanType.INDUSTRY_BENCHMARK_CONFIG; }
}
