package com.example.domain.objects.metadata;

import java.util.List;

import com.example.fiq.generic.FieldType;
import com.example.fiq.generic.GenericBeanFieldMetadata;
import com.example.fiq.generic.GenericBeanFieldMetadataBuilder;
import com.example.fiq.generic.GenericBeanMetadata;

public class IndustryBenchmarkConfigMetadata implements GenericBeanMetadata {
    private static final GenericBeanFieldMetadata<String> ID = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("id").label("Id").type(FieldType.STRING).required(false).updateAllowed(false).hidden(true)
            .sortSupported(true).filterSupported(true).build();

    public static final GenericBeanFieldMetadata<Long> CREATED_AT = GenericBeanFieldMetadataBuilder.<Long>builder()
            .name("createdAt").label("Created At").type(FieldType.EPOCH_MILLISECOND).updateAllowed(false)
            .required(false).sortSupported(true).filterSupported(true).build();

    public static final GenericBeanFieldMetadata<Long> MODIFIED_AT = GenericBeanFieldMetadataBuilder.<Long>builder()
            .name("modifiedAt").label("Modified At").type(FieldType.EPOCH_MILLISECOND).updateAllowed(false)
            .required(false).sortSupported(true).filterSupported(true).build();

    public static final GenericBeanFieldMetadata<String> INDUSTRY_NAME = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("industryName").label("Industry Name").type(FieldType.STRING).updateAllowed(false)
            .required(true).sortSupported(true).filterSupported(true).build();

    public static final GenericBeanFieldMetadata<String> COUNTRY = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("country").label("Country").type(FieldType.STRING).updateAllowed(false)
            .required(true).sortSupported(true).filterSupported(true).build();

    public static final GenericBeanFieldMetadata<String> SLUG = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("slug").label("Slug").type(FieldType.STRING).updateAllowed(false)
            .required(true).sortSupported(true).filterSupported(true).build();

    public static final GenericBeanFieldMetadata<String> STATUS = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("status").label("Status").type(FieldType.STRING).updateAllowed(true)
            .required(false).sortSupported(true).filterSupported(true).build();

    public static final GenericBeanFieldMetadata<List> COMPANIES = GenericBeanFieldMetadataBuilder.<List>builder()
            .name("companies").label("Companies").type(FieldType.LIST).updateAllowed(true)
            .required(false).sortSupported(false).filterSupported(false).build();

    @Override
    public List<GenericBeanFieldMetadata<?>> getFields() {
        return List.of(ID, CREATED_AT, MODIFIED_AT, INDUSTRY_NAME, COUNTRY, SLUG, STATUS, COMPANIES);
    }
}
