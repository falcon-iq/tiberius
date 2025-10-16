package com.example.fiq.generic;

public class GenericBeanFieldChangeItem<Type> {
    private String fieldName;
    private Type oldValue;
    private Type newValue;

    public GenericBeanFieldChangeItem() {
    }

    public GenericBeanFieldChangeItem(String fieldName, Type oldValue, Type newValue) {
        this.fieldName = fieldName;
        this.oldValue = oldValue;
        this.newValue = newValue;
    }

    public String getFieldName() {
        return fieldName;
    }

    public void setFieldName(String fieldName) {
        this.fieldName = fieldName;
    }

    public Type getOldValue() {
        return oldValue;
    }

    public void setOldValue(Type oldValue) {
        this.oldValue = oldValue;
    }

    public Type getNewValue() {
        return newValue;
    }

    public void setNewValue(Type newValue) {
        this.newValue = newValue;
    }
    
}
