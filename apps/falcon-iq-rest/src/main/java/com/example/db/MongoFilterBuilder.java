package com.example.db;

import com.example.fiq.generic.Filter;
import com.example.fiq.generic.FilterOperator;
import com.mongodb.client.model.Filters;
import org.bson.conversions.Bson;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Fluent builder for MongoDB Bson filters using your Filter/FilterOperator model.
 * Mirrors the semantics in your createFilterFromFilter(...) switch.
 */
public class MongoFilterBuilder {

    private final List<Bson> andParts = new ArrayList<>();

    // ---- Public API ---------------------------------------------------------

    /** AND a single Filter */
    public MongoFilterBuilder and(Filter filter) {
        andParts.add(toBson(filter));
        return this;
    }

    /** AND many Filters */
    public MongoFilterBuilder and(List<Filter> filters) {
        for (Filter f : filters) and(f);
        return this;
    }

    /** AND using field/operator/values directly */
    public MongoFilterBuilder and(String field, FilterOperator op, Object... values) {
        andParts.add(toBson(new Filter(field, op, Arrays.asList(values))));
        return this;
    }

    /**
     * AND an OR-group of filters: (f1 OR f2 OR ...).
     * Example:
     *   builder.orGroup(List.of(f1, f2)).and(f3).build()
     */
    public MongoFilterBuilder orGroup(List<Filter> filters) {
        if (filters == null || filters.isEmpty()) return this;
        List<Bson> ors = new ArrayList<>();
        for (Filter f : filters) {
            ors.add(toBson(f));
        }
        andParts.add(Filters.or(ors));
        return this;
    }

    /** Build final Bson */
    public Bson build() {
        if (andParts.isEmpty()) return Filters.empty();
        if (andParts.size() == 1) return andParts.get(0);
        return Filters.and(andParts);
    }

    // ---- Implementation -----------------------------------------------------

    private static Bson toBson(Filter filter) {
        final String field = filter.getField(); // assuming metadata field == DB field (per your TODO)
        if (field == null) {
            throw new UnsupportedOperationException("Field Name not found " + filter.getField());
        }

        final FilterOperator filterType = filter.getOperator();
        final List<Object> values = filter.getValues();

        switch (filterType) {
            case IN:
                return Filters.in(field, values);

            case NOT_IN:
                return Filters.nin(field, values);

            case EQUALS:
                return Filters.eq(field, first(values));

            case GREATER_THAN:
                return Filters.gt(field, first(values));

            case GREATER_THAN_EQUALS:
                return Filters.gte(field, first(values));

            case LESS_THAN:
                return Filters.lt(field, first(values));

            case LESS_THAN_EQUALS:
                return Filters.lte(field, first(values));

            case EXISTS:
                return Filters.exists(field, true);

            case MISSING:
                return Filters.exists(field, false);

            // Inclusive range if both present; one-sided if one bound is null
            case BETWEEN: {
                Object low  = values.size() > 0 ? values.get(0) : null;
                Object high = values.size() > 1 ? values.get(1) : null;

                List<Bson> parts = new ArrayList<>();
                if (low  != null) parts.add(Filters.gte(field, low));   // use gt for exclusive
                if (high != null) parts.add(Filters.lte(field, high));  // use lt for exclusive

                if (parts.isEmpty()) {
                    throw new IllegalArgumentException("BETWEEN requires at least one bound");
                }
                return parts.size() == 1 ? parts.get(0) : Filters.and(parts);
            }

            // Anchored, case-insensitive prefix
            case STARTS_WITH: {
                String term = String.valueOf(first(values));
                Pattern p = Pattern.compile("^" + Pattern.quote(term), Pattern.CASE_INSENSITIVE);
                return Filters.regex(field, p);
            }

            // Substring, case-insensitive
            case CONTAINS: {
                String term = String.valueOf(first(values));
                Pattern p = Pattern.compile(Pattern.quote(term), Pattern.CASE_INSENSITIVE);
                return Filters.regex(field, p);
            }

            default:
                throw new UnsupportedOperationException("Unknown filter type: " + filterType);
        }
    }

    private static Object first(List<Object> values) {
        if (values == null || values.isEmpty()) {
            throw new IllegalArgumentException("Missing value for filter");
        }
        return values.get(0);
    }
}
