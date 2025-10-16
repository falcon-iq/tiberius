package com.example.fiq.generic;

import java.util.List;
import com.example.db.MongoRepository;
import com.example.db.MongoFilterBuilder;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.bson.conversions.Bson;
import com.mongodb.client.model.Updates;
import java.util.ArrayList;

public class GenericMongoCRUDService<StoredObject> {
    private final MongoRepository<StoredObject> repository;

    public GenericMongoCRUDService(MongoRepository<StoredObject> repository) {
        this.repository = repository;
    }

    public List<StoredObject> list(List<Filter> filters, Sort sort, Page page, String searchString) {
        MongoFilterBuilder builder = new MongoFilterBuilder();
        Bson bsonFilter = builder.and(filters).build();

        List<StoredObject> results = repository.findAsPOJOs(bsonFilter);
        // Note: Sorting, pagination, and searchString handling would need to be
        // implemented here as well.
        return results;
    }

    public Boolean update(String id, List<GenericBeanFieldChangeItem<StoredObject>> changeItems) {
        if (id == null || id.isBlank())
            return false;
        if (changeItems == null || changeItems.isEmpty())
            return false;

        // build a combined update from changeItems
        List<Bson> sets = new ArrayList<>();
        for (GenericBeanFieldChangeItem<StoredObject> item : changeItems) {
            // TODO - validate field name against metadata and see if update is allowed
            if (item == null || item.getFieldName() == null)
                continue;
            sets.add(Updates.set(item.getFieldName(), item.getNewValue()));
        }

        if (sets.isEmpty())
            return false;

        Bson combined = Updates.combine(sets);
        return repository.updateById(id, combined);
    }

    public Boolean delete(String id) {
        if (id == null || id.isBlank()) return false;
        return repository.deleteById(id);
    }

    public StoredObject create(StoredObject object) {
        return repository.create(object);
    }

    public StoredObject createFromJson(JsonNode body, ObjectMapper mapper) {
        try {
            return create(mapper.treeToValue(body, repository.getMongoClass()));
        } catch (Exception e) {
            // TODO
            throw new RuntimeException("Failed to construct object from JSON", e);
        }
    }

    // @Override
    // public ListResponse<ReturnObject> getListResponse(List<Filter> filters, Sort
    // sort, Page page, String searchString) {
    // final Query query = getQuery(filters, sort, page, searchString);
    // final List<StoredObject> storedObjects = getMongoTemplate().find(query,
    // getMongoClass(), getCollectionName());
    // final Long count = getMongoTemplate().count(query, getMongoClass(),
    // getCollectionName());
    // final List<ReturnObject> returnObjects =
    // SprinklrCollectionUtils.transformToList(storedObjects, getTransformer());
    // return new ListResponse<>(decorate(filters, returnObjects), count);
    // }

    // @Override
    // public void delete(String id) {
    // final Query query = Query.query(Criteria.where("_id").is(id));
    // getMongoTemplate().remove(query, getMongoClass());
    // }

    // @Override
    // public void bulkDelete(List<String> ids) {
    // nullSafeList(ids).forEach(this::delete);
    // }

    // protected Query getQuery(List<Filter> filters, Sort sort, Page page, String
    // searchString) {
    // final Criteria criteria = getCriteria(filters, searchString);

    // return getQueryForCriteria(sort, page, criteria);
    // }

    // @SuppressWarnings("Duplicates")
    // protected Query getQueryForCriteria(Sort sort, Page page, Criteria criteria)
    // {
    // final Query query = Query.query(criteria);
    // if (page != null) {
    // query.skip(page.start());
    // query.limit(page.getSize());
    // }

    // if (sort != null) {
    // final String key = sort.getKey();
    // boolean isSortSupported = isSortSupported(key);
    // if (!isSortSupported) {
    // throw new UnsupportedOperationException("Sort not supported " + key);
    // }

    // final String filterFieldName = getFilterFieldName(key);
    // if (key == null) {
    // throw new UnsupportedOperationException("Field Name not found " +
    // filterFieldName);
    // }

    // query.with(new org.springframework.data.domain.Sort(sort.getOrder() ==
    // Order.ASC ? ASC : DESC,
    // filterFieldName));
    // }
    // return query;
    // }

    // @SuppressWarnings("Duplicates")
    // protected Criteria getCriteria(List<Filter> filters, String searchString) {
    // final List<Filter> finalFilters = Lists.newArrayList();
    // final List<Filter> additionalFilters = getAdditionalFilters(filters);
    // if (CollectionUtils.isNotEmpty(additionalFilters)) {
    // finalFilters.addAll(additionalFilters);
    // }

    // if (CollectionUtils.isNotEmpty(filters)) {
    // finalFilters.addAll(filters);
    // }

    // final List<Criteria> orCriterias = Lists.newArrayList();
    // final List<Filter> orFilters = getOrFilters();
    // for (Filter orFilter : nullSafeList(orFilters)) {
    // Criteria orCriteria = createCriteria(Lists.newArrayList(orFilter), null);
    // orCriterias.add(orCriteria);
    // }

    // Criteria criteria = createCriteria(finalFilters, searchString);
    // if (CollectionUtils.isNotEmpty(orCriterias)) {
    // criteria = new Criteria().andOperator(criteria,
    // new Criteria().orOperator(orCriterias.toArray(new Criteria[0])));
    // }

    // return criteria;
    // }

    // protected Criteria createCriteria(List<Filter> filters, String searchString)
    // {
    // Criteria criteria = null;
    // for (Filter filter : nullSafeList(filters)) {
    // criteria = createCriteriaFromFilter(criteria, filter);
    // }

    // if (StringUtils.isNotBlank(searchString) &&
    // CollectionUtils.isNotEmpty(getSearchableFields())) {
    // final Set<String> searchableFields = getSearchableFields();
    // final Pattern pattern = Pattern.compile(Pattern.quote(searchString),
    // Pattern.CASE_INSENSITIVE);

    // final List<Criteria> Filters = Lists.newArrayList();
    // for (String searchableField : searchableFields) {
    // if (isOnlyExactMatchSupported(searchableField)) {
    // Criteria inFilter = Criteria.where(searchableField).is(searchString);
    // Filters.add(inFilter);

    // } else {
    // Criteria regexFilter = Criteria.where(searchableField).regex(pattern);
    // Filters.add(regexFilter);
    // }
    // }

    // if (criteria == null) {
    // criteria = new Criteria();
    // }
    // if (CollectionUtils.isNotEmpty(Filters)) {
    // criteria.orOperator(Filters.toArray(new Criteria[0]));
    // }
    // }
    // return (criteria == null) ? new Criteria() : criteria;
    // }
}
