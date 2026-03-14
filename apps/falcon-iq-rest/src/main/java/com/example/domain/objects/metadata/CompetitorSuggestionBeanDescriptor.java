package com.example.domain.objects.metadata;

import com.example.domain.objects.CompetitorSuggestion;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class CompetitorSuggestionBeanDescriptor implements GenericBeanDescriptor<CompetitorSuggestion> {

    @Override
    public String getMongoCollectionName() {
        return "competitor_suggestion";
    }

    @Override
    public String getMongoDatabaseName() {
        return "company_db";
    }

    @Override
    public Class<CompetitorSuggestion> getDomainObjectClazz() {
        return CompetitorSuggestion.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return null;
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.COMPETITOR_SUGGESTION;
    }
}
