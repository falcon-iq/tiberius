package com.example.fiq.generic;

import java.util.List;

public interface GenericBeanMetadata {
    List<GenericBeanFieldMetadata<?>> getFields();
}
