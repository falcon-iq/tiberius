package com.example.domain.objects.metadata;

import com.example.domain.objects.CompanyProfile;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class CompanyProfileBeanDescriptor implements GenericBeanDescriptor<CompanyProfile> {

    @Override
    public String getMongoCollectionName() {
        return "company_profile";
    }

    @Override
    public String getMongoDatabaseName() {
        return "company_db";
    }

    @Override
    public Class<CompanyProfile> getDomainObjectClazz() {
        return CompanyProfile.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return new CompanyProfileMetadata();
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.COMPANY_PROFILE;
    }
}
