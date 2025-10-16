package com.example.domain.objects.metadata;

import java.util.List;

import com.example.fiq.generic.FieldType;
import com.example.fiq.generic.GenericBeanFieldMetadata;
import com.example.fiq.generic.GenericBeanFieldMetadataBuilder;
import com.example.fiq.generic.GenericBeanMetadata;

public class OKRStatusMetadata implements GenericBeanMetadata {
    private static final GenericBeanFieldMetadata<String> ID = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("_id")
            .label("Id")
            .type(FieldType.STRING)
            .required(false)
            .updateAllowed(false)
            .hidden(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<String> STATUS = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("status")
            .label("Status")
            .type(FieldType.STRING)
            .updateAllowed(true)
            .required(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    @Override
    public List<GenericBeanFieldMetadata<?>> getFields() {
        return List.of(ID, STATUS);
    }
}
