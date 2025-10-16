package com.example.fiq.generic;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import com.example.db.MongoRepository;
import com.example.domain.objects.metadata.OKRBeanDescriptor;
import com.example.domain.objects.metadata.OKRStatusBeanDescriptor;
import com.example.domain.objects.metadata.UserProfileBeanDescriptor;

public class GenericBeanDescriptorFactory {
    private static final GenericBeanDescriptorFactory INSTANCE = new GenericBeanDescriptorFactory();

    static {
        GenericBeanDescriptorFactory.getInstance().register(GenericBeanType.OKR, new OKRBeanDescriptor());
        GenericBeanDescriptorFactory.getInstance().register(GenericBeanType.OKR_STATUS, new OKRStatusBeanDescriptor());
        GenericBeanDescriptorFactory.getInstance().register(GenericBeanType.USER_PROFILE, new UserProfileBeanDescriptor());
    }
    
    private final Map<GenericBeanType, GenericBeanDescriptor<?>> descriptors = new ConcurrentHashMap<>();
    // cache services so we don't create a new GenericMongoCRUDService on each
    // request
    private final Map<GenericBeanType, GenericMongoCRUDService<?>> crudServiceCache = new ConcurrentHashMap<>();

    private GenericBeanDescriptorFactory() {
    }

    public static GenericBeanDescriptorFactory getInstance() {
        return INSTANCE;
    }

    public GenericBeanDescriptor<?> getDescriptor(GenericBeanType type) {
        return descriptors.get(type);
    }

    public void register(GenericBeanType beanType, GenericBeanDescriptor<?> beanDescriptor) {
        descriptors.put(beanType, beanDescriptor);
    }

    public GenericMongoCRUDService<?> getCRUDService(GenericBeanType type) {
        GenericBeanDescriptor<?> descriptor = getDescriptor(type);
        if (descriptor == null) {
            throw new IllegalArgumentException("No descriptor registered for type: " + type);
        }

        MongoRepository<?> repo = new MongoRepository<>(descriptor.getMongoCollectionName(),
                descriptor.getMongoDatabaseName(), descriptor.getDomainObjectClazz());
        return crudServiceCache.computeIfAbsent(type, t -> new GenericMongoCRUDService<>(repo));
    }
}