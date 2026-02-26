package com.example.domain.objects;

import org.bson.BsonType;
import org.bson.codecs.pojo.annotations.BsonId;
import org.bson.codecs.pojo.annotations.BsonRepresentation;

public abstract class AbstractBaseDomainObject {
    public static final String ID = "id";
    public static final String CREATED_AT = "createdAt";
    public static final String MODIFIED_AT = "modifiedAt";

    @BsonId
    @BsonRepresentation(BsonType.OBJECT_ID)
    private String id;

    private Long createdAt;

    private Long modifiedAt;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public Long getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Long createdAt) {
        this.createdAt = createdAt;
    }

    public Long getModifiedAt() {
        return modifiedAt;
    }

    public void setModifiedAt(Long modifiedAt) {
        this.modifiedAt = modifiedAt;
    }
}
