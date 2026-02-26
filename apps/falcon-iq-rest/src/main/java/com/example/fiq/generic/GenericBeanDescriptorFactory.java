package com.example.fiq.generic;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import com.example.db.MongoRepository;
import com.example.domain.objects.metadata.BenchmarkReportTaskBeanDescriptor;
import com.example.domain.objects.metadata.CompanyProfileBeanDescriptor;

import com.example.domain.objects.metadata.UserProfileBeanDescriptor;
import com.example.domain.objects.metadata.WebsiteCrawlDetailBeanDescriptor;

public class GenericBeanDescriptorFactory {
    private static final GenericBeanDescriptorFactory INSTANCE = new GenericBeanDescriptorFactory();

    static {
        GenericBeanDescriptorFactory.getInstance().register(GenericBeanType.USER_PROFILE,
                new UserProfileBeanDescriptor());
        GenericBeanDescriptorFactory.getInstance().register(GenericBeanType.WEBSITE_CRAWL_DETAIL,
                new WebsiteCrawlDetailBeanDescriptor());
        GenericBeanDescriptorFactory.getInstance().register(GenericBeanType.COMPANY_PROFILE,
                new CompanyProfileBeanDescriptor());
        GenericBeanDescriptorFactory.getInstance().register(GenericBeanType.BENCHMARK_REPORT_TASK,
                new BenchmarkReportTaskBeanDescriptor());
    }

    private final Map<GenericBeanType, GenericBeanDescriptor<? extends com.example.domain.objects.AbstractBaseDomainObject>> descriptors = new ConcurrentHashMap<>();
    // cache services so we don't create a new GenericMongoCRUDService on each
    // request
    private final Map<GenericBeanType, GenericMongoCRUDService<? extends com.example.domain.objects.AbstractBaseDomainObject>> crudServiceCache = new ConcurrentHashMap<>();

    private GenericBeanDescriptorFactory() {
    }

    public static GenericBeanDescriptorFactory getInstance() {
        return INSTANCE;
    }

    public GenericBeanDescriptor<? extends com.example.domain.objects.AbstractBaseDomainObject> getDescriptor(GenericBeanType type) {
        return descriptors.get(type);
    }

    public <T extends com.example.domain.objects.AbstractBaseDomainObject> void register(GenericBeanType beanType, GenericBeanDescriptor<T> beanDescriptor) {
        descriptors.put(beanType, beanDescriptor);
    }

    @SuppressWarnings("unchecked")
    public <T extends com.example.domain.objects.AbstractBaseDomainObject> GenericMongoCRUDService<T> getCRUDService(GenericBeanType type) {
        return (GenericMongoCRUDService<T>) crudServiceCache.computeIfAbsent(type, t -> {
            GenericBeanDescriptor<T> descriptor = (GenericBeanDescriptor<T>) getDescriptor(t);
            if (descriptor == null) {
                throw new IllegalArgumentException("No descriptor registered for type: " + t);
            }
            MongoRepository<T> repo = new MongoRepository<>(descriptor.getMongoCollectionName(),
                    descriptor.getMongoDatabaseName(), descriptor.getDomainObjectClazz());
            return new GenericMongoCRUDService<>(repo);
        });
    }
}