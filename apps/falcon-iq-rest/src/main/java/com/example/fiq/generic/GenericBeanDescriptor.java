package com.example.fiq.generic;

public interface GenericBeanDescriptor<T> {
    String getMongoCollectionName();

    String getMongoDatabaseName();

    Class<T> getDomainObjectClazz();

    GenericBeanMetadata getGenericBeanMetadata();

    GenericBeanType getType();
}
