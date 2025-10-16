package com.example.api;

import java.util.List;

import com.example.fiq.generic.Filter;
import com.example.fiq.generic.Page;

/**
 * Simple DTO representing a generic read request carrying filters, paging
 * and a free-text search string.
 */
public class GenericReadRequest {

	private Page page;
	private String searchString;
	private List<Filter> filters;

	public GenericReadRequest() {
	}

	public GenericReadRequest(Page page, String searchString, List<Filter> filters) {
		this.page = page;
		this.searchString = searchString;
		this.filters = filters;
	}

	public Page getPage() {
		return page;
	}

	public void setPage(Page page) {
		this.page = page;
	}

	public String getSearchString() {
		return searchString;
	}

	public void setSearchString(String searchString) {
		this.searchString = searchString;
	}

	public List<Filter> getFilters() {
		return filters;
	}

	public void setFilters(List<Filter> filters) {
		this.filters = filters;
	}
}
