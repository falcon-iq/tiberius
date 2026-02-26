package com.example.domain.objects.metadata;

import java.util.List;

import com.example.fiq.generic.FieldType;
import com.example.fiq.generic.GenericBeanFieldMetadata;
import com.example.fiq.generic.GenericBeanFieldMetadataBuilder;
import com.example.fiq.generic.GenericBeanMetadata;

public class CompanyProfileMetadata implements GenericBeanMetadata {
    private static final GenericBeanFieldMetadata<String> ID = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("id")
            .label("Id")
            .type(FieldType.STRING)
            .required(false)
            .updateAllowed(false)
            .hidden(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<String> COMPANY_NAME = GenericBeanFieldMetadataBuilder
            .<String>builder()
            .name("companyName")
            .label("Company Name")
            .type(FieldType.STRING)
            .updateAllowed(true)
            .required(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<String> VERTICAL = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("vertical")
            .label("Vertical")
            .type(FieldType.STRING)
            .updateAllowed(true)
            .required(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<Long> CREATED_AT = GenericBeanFieldMetadataBuilder.<Long>builder()
            .name("createdAt")
            .label("Created At")
            .type(FieldType.EPOCH_MILLISECOND)
            .updateAllowed(false)
            .required(false)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<Long> MODIFIED_AT = GenericBeanFieldMetadataBuilder.<Long>builder()
            .name("modifiedAt")
            .label("Modified At")
            .type(FieldType.EPOCH_MILLISECOND)
            .updateAllowed(false)
            .required(false)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    @Override
    public List<GenericBeanFieldMetadata<?>> getFields() {
        return List.of(ID, COMPANY_NAME, VERTICAL, CREATED_AT, MODIFIED_AT);
    }
}
