package com.example.fiq.generic;

public interface CustomValidator<Type> {
    boolean validate(Object value);
}
