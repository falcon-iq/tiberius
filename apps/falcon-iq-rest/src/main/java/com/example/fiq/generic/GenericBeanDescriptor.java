package com.example.fiq.generic;

import com.example.domain.objects.AbstractBaseDomainObject;

public interface GenericBeanDescriptor<T extends AbstractBaseDomainObject> {
    String getMongoCollectionName();

    String getMongoDatabaseName();

    Class<T> getDomainObjectClazz();

    GenericBeanMetadata getGenericBeanMetadata();

    GenericBeanType getType();
}
