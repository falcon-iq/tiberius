package com.example.domain.objects.metadata;

import com.example.domain.objects.BenchmarkRequestEvent;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class BenchmarkRequestEventBeanDescriptor implements GenericBeanDescriptor<BenchmarkRequestEvent> {

    @Override
    public String getMongoCollectionName() {
        return "benchmark_request_events";
    }

    @Override
    public String getMongoDatabaseName() {
        return "company_db";
    }

    @Override
    public Class<BenchmarkRequestEvent> getDomainObjectClazz() {
        return BenchmarkRequestEvent.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return null;
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.BENCHMARK_REQUEST_EVENT;
    }
}
