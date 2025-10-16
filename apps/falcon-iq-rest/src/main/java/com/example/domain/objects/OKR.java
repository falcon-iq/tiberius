package com.example.domain.objects;

import org.bson.BsonType;
import org.bson.codecs.pojo.annotations.BsonId;
import org.bson.codecs.pojo.annotations.BsonProperty;
import org.bson.codecs.pojo.annotations.BsonRepresentation;

import java.util.List;

public class OKR {
    public static final String ID = "id";
    public static final String OBJECTIVE = "objective";
    public static final String KEY_RESULTS = "keyResults";
    public static final String OWNER = "owner";
    public static final String QUARTER = "quarter";

    @BsonId
    @BsonRepresentation(BsonType.OBJECT_ID)
    private String id;

    private String objective;

    @BsonProperty("key_results")
    private List<String> keyResults;

    private String owner;

    private String quarter;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getObjective() {
        return objective;
    }

    public void setObjective(String objective) {
        this.objective = objective;
    }

    public List<String> getKeyResults() {
        return keyResults;
    }

    public void setKeyResults(List<String> keyResults) {
        this.keyResults = keyResults;
    }

    public String getOwner() {
        return owner;
    }

    public void setOwner(String owner) {
        this.owner = owner;
    }

    public String getQuarter() {
        return quarter;
    }

    public void setQuarter(String quarter) {
        this.quarter = quarter;
    }

    @Override
    public String toString() {
        String idHex = (id == null) ? "null" : id;
        return "OKR{" +
                "_id='" + idHex + '\'' +
                ", objective='" + objective + '\'' +
                ", keyResults=" + keyResults +
                ", owner='" + owner + '\'' +
                ", quarter='" + quarter + '\'' +
                '}';
    }
}