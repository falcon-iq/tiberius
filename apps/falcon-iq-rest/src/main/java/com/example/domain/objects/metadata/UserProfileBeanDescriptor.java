package com.example.domain.objects.metadata;

import com.example.domain.objects.UserProfile;
import com.example.fiq.generic.GenericBeanDescriptor;
import com.example.fiq.generic.GenericBeanMetadata;
import com.example.fiq.generic.GenericBeanType;

public class UserProfileBeanDescriptor implements GenericBeanDescriptor<UserProfile> {
            
    @Override
    public String getMongoCollectionName() {
        return "user_profile";
    }

    @Override
    public String getMongoDatabaseName() {
        return "okrsdb";
    }

    @Override
    public Class<UserProfile> getDomainObjectClazz() {
        return UserProfile.class;
    }

    @Override
    public GenericBeanMetadata getGenericBeanMetadata() {
        return new UserProfileMetadata();
    }

    @Override
    public GenericBeanType getType() {
        return GenericBeanType.USER_PROFILE;
    }
}
