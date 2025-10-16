package com.example.fiq.generic;

/**
 * External builder for GenericBeanFieldMetadata to avoid keeping builder inside the model class.
 */
public final class GenericBeanFieldMetadataBuilder<T> {
    private final GenericBeanFieldMetadata<T> m = new GenericBeanFieldMetadata<>();

    public static <T> GenericBeanFieldMetadataBuilder<T> builder() {
        return new GenericBeanFieldMetadataBuilder<>();
    }

    public GenericBeanFieldMetadataBuilder<T> name(String name) {
        m.setName(name);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> label(String label) {
        m.setLabel(label);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> type(FieldType type) {
        m.setType(type);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> required(Boolean required) {
        m.setIsRequired(required);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> defaultValue(T defaultValue) {
        m.setDefaultValue(defaultValue);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> updateAllowed(Boolean updateAllowed) {
        m.setIsUpdateAllowed(updateAllowed);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> customValidator(CustomValidator<T> validator) {
        m.setCustomValidator(validator);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> sortSupported(Boolean sortSupported) {
        m.setIsSortSupported(sortSupported);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> filterSupported(Boolean filterSupported) {
        m.setIsFilterSupported(filterSupported);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> hidden(Boolean hidden) {
        m.setIsHidden(hidden);
        return this;
    }

    public GenericBeanFieldMetadataBuilder<T> lookupKey(String lookupKey) {
        m.setLookupKey(lookupKey);
        return this;
    }

    public GenericBeanFieldMetadata<T> build() {
        return m;
    }
}
