package com.example.domain.objects.metadata;

import java.util.List;

import com.example.fiq.generic.FieldType;
import com.example.fiq.generic.GenericBeanFieldMetadata;
import com.example.fiq.generic.GenericBeanFieldMetadataBuilder;
import com.example.fiq.generic.GenericBeanMetadata;

public class BenchmarkReportTaskMetadata implements GenericBeanMetadata {
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

        public static final GenericBeanFieldMetadata<String> COMPANY_ID = GenericBeanFieldMetadataBuilder
                        .<String>builder()
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

        public static final GenericBeanFieldMetadata<String> MY_WEBSITE_CRAWL_DETAIL_ID = GenericBeanFieldMetadataBuilder
                        .<String>builder()
                        .name("myWebsiteCrawlDetailId")
                        .label("My Website Crawl Detail Id")
                        .type(FieldType.STRING)
                        .updateAllowed(true)
                        .required(true)
                        .sortSupported(true)
                        .filterSupported(true)
                        .build();

        public static final GenericBeanFieldMetadata<List> MY_COMPETITION_CRAWL_DETAIL_IDS = GenericBeanFieldMetadataBuilder
                        .<List>builder()
                        .name("myCompetitionCrawlDetailIds")
                        .label("Competition Crawl Detail Ids")
                        .type(FieldType.LIST)
                        .updateAllowed(true)
                        .required(false)
                        .sortSupported(false)
                        .filterSupported(false)
                        .build();

        public static final GenericBeanFieldMetadata<Number> TOTAL_TASKS = GenericBeanFieldMetadataBuilder
                        .<Number>builder()
                        .name("totalTasks")
                        .label("Total Tasks")
                        .type(FieldType.NUMBER)
                        .updateAllowed(true)
                        .required(false)
                        .sortSupported(true)
                        .filterSupported(true)
                        .build();

        public static final GenericBeanFieldMetadata<Number> PROGRESS = GenericBeanFieldMetadataBuilder
                        .<Number>builder()
                        .name("progress")
                        .label("Progress")
                        .type(FieldType.NUMBER)
                        .updateAllowed(true)
                        .required(false)
                        .sortSupported(true)
                        .filterSupported(true)
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

        @Override
        public List<GenericBeanFieldMetadata<?>> getFields() {
                return List.of(ID, COMPANY_ID, USER_ID, CREATED_AT, MODIFIED_AT, MY_WEBSITE_CRAWL_DETAIL_ID,
                                MY_COMPETITION_CRAWL_DETAIL_IDS, TOTAL_TASKS, PROGRESS, REPORT_URL);
        }
}
