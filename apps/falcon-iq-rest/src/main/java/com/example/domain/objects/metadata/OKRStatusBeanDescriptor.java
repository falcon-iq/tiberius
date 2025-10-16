package com.example.domain.objects.metadata;

import com.example.domain.objects.OKRStatus;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class OKRStatusBeanDescriptor implements GenericBeanDescriptor<OKRStatus> {
            
    @Override
    public String getMongoCollectionName() {
        return "okr_statuses";
    }

    @Override
    public String getMongoDatabaseName() {
        return "okrsdb";
    }

    @Override
    public Class<OKRStatus> getDomainObjectClazz() {
        return OKRStatus.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return new OKRStatusMetadata();
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.OKR_STATUS;
    }
}
