package com.example.fiq.generic;

public class Sort {
    private String key;
    private Order order;

    public Sort(String key, Order order) {
        this.key = key;
        this.order = order;
    }

    public String getKey() {
        return key;
    }

    public Order getOrder() {
        return order;
    }

    public enum Order {
        ASC, DESC
    }
}
