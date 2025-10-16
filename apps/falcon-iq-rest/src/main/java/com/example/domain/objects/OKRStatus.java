package com.example.domain.objects;

import org.bson.BsonType;
import org.bson.codecs.pojo.annotations.BsonId;
import org.bson.codecs.pojo.annotations.BsonRepresentation;

public class OKRStatus {
    public static final String ID = "id";
    public static final String STATUS = "status";

    @BsonId
    @BsonRepresentation(BsonType.OBJECT_ID)
    private String id;

    private String status;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }


}