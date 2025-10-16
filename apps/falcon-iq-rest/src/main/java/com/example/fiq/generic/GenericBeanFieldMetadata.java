package com.example.fiq.generic;

import com.fasterxml.jackson.annotation.JsonIgnore;

public class GenericBeanFieldMetadata<Type> implements Cloneable {
    private String name;
    private String label;
    private FieldType type;

    // write configuration
    private Boolean isRequired;
    private Type defaultValue;

    // update configuration
    private Boolean isUpdateAllowed;
    private CustomValidator<Type> customValidator;

    // read configuration
    private Boolean isSortSupported;
    private Boolean isFilterSupported;
    private Boolean isHidden;
    private String lookupKey;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label;
    }

    public FieldType getType() {
        return type;
    }

    public void setType(FieldType type) {
        this.type = type;
    }

    public Boolean getIsSortSupported() {
        return isSortSupported;
    }

    public void setIsSortSupported(Boolean isSortSupported) {
        this.isSortSupported = isSortSupported;
    }

    public Boolean getIsFilterSupported() {
        return isFilterSupported;
    }

    public void setIsFilterSupported(Boolean isFilterSupported) {
        this.isFilterSupported = isFilterSupported;
    }

    public String getLookupKey() {
        return lookupKey;
    }

    public void setLookupKey(String lookupKey) {
        this.lookupKey = lookupKey;
    }
    
    public Boolean getIsHidden() {
        return isHidden;
    }

    public void setIsHidden(Boolean isHidden) {
        this.isHidden = isHidden;
    }

    public Boolean getIsRequired() {
        return isRequired;
    }

    public void setIsRequired(Boolean isRequired) {
        this.isRequired = isRequired;
    }

    public Type getDefaultValue() {
        return defaultValue;
    }

    public void setDefaultValue(Type defaultValue) {
        this.defaultValue = defaultValue;
    }

    public Boolean getIsUpdateAllowed() {
        return isUpdateAllowed;
    }

    public void setIsUpdateAllowed(Boolean isUpdateAllowed) {
        this.isUpdateAllowed = isUpdateAllowed;
    }

    @JsonIgnore
    public CustomValidator<Type> getCustomValidator() {
        return customValidator;
    }

    @JsonIgnore
    public void setCustomValidator(CustomValidator<Type> customValidator) {
        this.customValidator = customValidator;
    }
}
