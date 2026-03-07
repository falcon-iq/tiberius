package com.example.domain.objects.metadata;

import java.util.List;

import com.example.fiq.generic.FieldType;
import com.example.fiq.generic.GenericBeanFieldMetadata;
import com.example.fiq.generic.GenericBeanFieldMetadataBuilder;
import com.example.fiq.generic.GenericBeanMetadata;

public class CompanyBenchmarkReportMetadata implements GenericBeanMetadata {
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

        public static final GenericBeanFieldMetadata<String> USER_ID = GenericBeanFieldMetadataBuilder.<String>builder()
                        .name("userId")
                        .label("User Id")
                        .type(FieldType.STRING)
                        .updateAllowed(false)
                        .required(true)
                        .sortSupported(true)
                        .filterSupported(true)
                        .build();

        public static final GenericBeanFieldMetadata<String> COMPANY_CRAWL_DETAIL_ID = GenericBeanFieldMetadataBuilder
                        .<String>builder()
                        .name("companyCrawlDetailId")
                        .label("Company Crawl Detail Id")
                        .type(FieldType.STRING)
                        .updateAllowed(true)
                        .required(true)
                        .sortSupported(true)
                        .filterSupported(true)
                        .build();

        public static final GenericBeanFieldMetadata<List> COMPETITION_CRAWL_DETAIL_IDS = GenericBeanFieldMetadataBuilder
                        .<List>builder()
                        .name("competitionCrawlDetailIds")
                        .label("Competition Crawl Detail Ids")
                        .type(FieldType.LIST)
                        .updateAllowed(true)
                        .required(false)
                        .sortSupported(false)
                        .filterSupported(false)
                        .build();

        public static final GenericBeanFieldMetadata<String> REPORT_URL = GenericBeanFieldMetadataBuilder
                        .<String>builder()
                        .name("reportUrl")
                        .label("Report URL")
                        .type(FieldType.STRING)
                        .updateAllowed(true)
                        .required(false)
                        .sortSupported(false)
                        .filterSupported(false)
                        .build();

        public static final GenericBeanFieldMetadata<String> STATUS = GenericBeanFieldMetadataBuilder.<String>builder()
                        .name("status")
                        .label("Status")
                        .type(FieldType.STRING)
                        .updateAllowed(true)
                        .required(false)
                        .sortSupported(true)
                        .filterSupported(true)
                        .build();

        @Override
        public List<GenericBeanFieldMetadata<?>> getFields() {
                return List.of(ID, CREATED_AT, MODIFIED_AT, USER_ID, COMPANY_CRAWL_DETAIL_ID,
                                COMPETITION_CRAWL_DETAIL_IDS, REPORT_URL, STATUS);
        }
}
