package com.example.domain.objects.metadata;

import com.example.domain.objects.OKR;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class OKRBeanDescriptor implements GenericBeanDescriptor<OKR> {
    
    @Override
    public String getMongoCollectionName() {
        return "objectives";
    }

    @Override
    public String getMongoDatabaseName() {
        return "okrsdb";
    }

    @Override
    public Class<OKR> getDomainObjectClazz() {
        return OKR.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return new OKRMetadata();
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.OKR;
    }
}
