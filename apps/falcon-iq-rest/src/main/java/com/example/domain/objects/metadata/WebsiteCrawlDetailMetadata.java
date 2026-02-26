package com.example.domain.objects.metadata;

import java.util.List;

import com.example.fiq.generic.FieldType;
import com.example.fiq.generic.GenericBeanFieldMetadata;
import com.example.fiq.generic.GenericBeanFieldMetadataBuilder;
import com.example.fiq.generic.GenericBeanMetadata;

public class WebsiteCrawlDetailMetadata implements GenericBeanMetadata {
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

    public static final GenericBeanFieldMetadata<String> COMPANY_ID = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("companyId")
            .label("Company Id")
            .type(FieldType.STRING)
            .updateAllowed(false)
            .required(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<String> USER_ID = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("userId")
            .label("User Id")
            .type(FieldType.STRING)
            .updateAllowed(false)
            .required(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<String> WEBSITE_LINK = GenericBeanFieldMetadataBuilder
            .<String>builder()
            .name("websiteLink")
            .label("Website Link")
            .type(FieldType.STRING)
            .updateAllowed(false)
            .required(true)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<Boolean> IS_COMPETITOR = GenericBeanFieldMetadataBuilder
            .<Boolean>builder()
            .name("isCompetitor")
            .label("Is Competitor")
            .type(FieldType.BOOLEAN)
            .updateAllowed(true)
            .required(false)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<Number> NUMBER_OF_PAGES_CRAWLED = GenericBeanFieldMetadataBuilder
            .<Number>builder()
            .name("numberOfPagesCrawled")
            .label("Number Of Pages Crawled")
            .type(FieldType.NUMBER)
            .updateAllowed(true)
            .required(false)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<Number> NUMBER_OF_PAGES_ANALYZED = GenericBeanFieldMetadataBuilder
            .<Number>builder()
            .name("numberOfPagesAnalyzed")
            .label("Number Of Pages Analyzed")
            .type(FieldType.NUMBER)
            .updateAllowed(true)
            .required(false)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<Number> TOTAL_PAGES = GenericBeanFieldMetadataBuilder
            .<Number>builder()
            .name("totalPages")
            .label("Total Pages")
            .type(FieldType.NUMBER)
            .updateAllowed(true)
            .required(false)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<String> STATUS = GenericBeanFieldMetadataBuilder.<String>builder()
            .name("status")
            .label("Status")
            .type(FieldType.STRING)
            .updateAllowed(false)
            .required(false)
            .sortSupported(true)
            .filterSupported(true)
            .build();

    public static final GenericBeanFieldMetadata<String> ERROR_MESSAGE = GenericBeanFieldMetadataBuilder
            .<String>builder()
            .name("errorMessage")
            .label("Error Message")
            .type(FieldType.STRING)
            .updateAllowed(true)
            .required(false)
            .sortSupported(false)
            .filterSupported(false)
            .build();

    public static final GenericBeanFieldMetadata<String> CRAWLED_PAGES_PATH = GenericBeanFieldMetadataBuilder
            .<String>builder()
            .name("crawledPagesPath")
            .label("Crawled Pages Path")
            .type(FieldType.STRING)
            .updateAllowed(true)
            .required(false)
            .sortSupported(false)
            .filterSupported(false)
            .build();

    @Override
    public List<GenericBeanFieldMetadata<?>> getFields() {
        return List.of(ID, CREATED_AT, MODIFIED_AT, COMPANY_ID, USER_ID, WEBSITE_LINK, IS_COMPETITOR,
                NUMBER_OF_PAGES_CRAWLED, NUMBER_OF_PAGES_ANALYZED, TOTAL_PAGES, STATUS, ERROR_MESSAGE,
                CRAWLED_PAGES_PATH);
    }
}
