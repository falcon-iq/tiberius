package com.example.fiq.generic;

import java.util.List;

public class Filter {
    private String field;
    private FilterOperator operator;
    private List<Object> values;

    public Filter() {
    }

    public Filter(String field, FilterOperator operator, List<Object> values) {
        this.field = field;
        this.operator = operator;
        this.values = values;
    }

    public String getField() {
        return field;
    }

    public void setField(String field) {
        this.field = field;
    }

    public FilterOperator getOperator() {
        return operator;
    }

    public void setOperator(FilterOperator operator) {
        this.operator = operator;
    }

    public List<Object> getValues() {
        return values;
    }

    public void setValues(List<Object> values) {
        this.values = values;
    }
}
