package com.example.domain.objects;

import org.bson.BsonType;
import org.bson.codecs.pojo.annotations.BsonId;
import org.bson.codecs.pojo.annotations.BsonRepresentation;

public class UserProfile {
    public static final String ID = "id";
    public static final String NAME = "name";
    public static final String EMAIL = "email";

    @BsonId
    @BsonRepresentation(BsonType.OBJECT_ID)
    private String id;

    private String name;

    private String email;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

}