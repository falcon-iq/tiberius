package com.example.domain.objects.metadata;

import com.example.domain.objects.WebsiteCrawlDetail;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class WebsiteCrawlDetailBeanDescriptor implements GenericBeanDescriptor<WebsiteCrawlDetail> {

    @Override
    public String getMongoCollectionName() {
        return "website_crawl_detail";
    }

    @Override
    public String getMongoDatabaseName() {
        return "company_db";
    }

    @Override
    public Class<WebsiteCrawlDetail> getDomainObjectClazz() {
        return WebsiteCrawlDetail.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return new WebsiteCrawlDetailMetadata();
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.WEBSITE_CRAWL_DETAIL;
    }
}
