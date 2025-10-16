package com.example.fiq.generic;

public class Page {
    private int size;
    private int pageNumber;

    public Page(int size, int pageNumber) {
        this.size = size;
        this.pageNumber = pageNumber;
    }

    public int getSize() {
        return size;
    }

    public int getPageNumber() {
        return pageNumber;
    }

    public int start() {
        return pageNumber * size;
    }

    public int end() {
        return start() + size;
    }
}
