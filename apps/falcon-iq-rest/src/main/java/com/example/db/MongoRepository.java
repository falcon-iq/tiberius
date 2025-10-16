package com.example.db;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.bson.Document;
import org.bson.conversions.Bson;
import org.bson.types.ObjectId;

import com.mongodb.client.FindIterable;
import com.mongodb.client.result.UpdateResult;
import com.mongodb.client.result.DeleteResult;
import com.mongodb.client.model.Filters;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoCollection;

public class MongoRepository<T> {
  private String collectionName;
  private String databaseName;
  private Class<T> mongoClass;

  public MongoRepository(String collectionName, String databaseName, Class<T> mongoClass) {
    this.collectionName = collectionName;
    this.databaseName = databaseName;
    this.mongoClass = mongoClass;
  }

  /**
   * Find an objective by its _id. Accepts either a 24-hex ObjectId string or any
   * other string
   * that matches a stored _id value.
   *
   * Returns Optional.empty() if not found or if the provided id is null/blank.
   */
  public Optional<T> findById(String id) {
    if (id == null || id.isBlank())
      return Optional.empty();

    // Try ObjectId first if it looks like one
    Document filter;
    if (ObjectId.isValid(id)) {
      filter = new Document("_id", new ObjectId(id));
    } else {
      filter = new Document("_id", id);
    }
    MongoCollection<T> collection = getCollection();

    FindIterable<T> coll = collection.find(filter).limit(1);
    T found = coll.first();
    return Optional.ofNullable(found);
  }

  public List<T> findAsPOJOs(Bson filter) {
    // TODO - support sort, paging, text search
    // need to ensure indexes are there for filterable fields and indexing is done in the right order

    MongoCollection<T> collection = getCollection();
    List<T> results = new ArrayList<>();
    FindIterable<T> coll = collection.find(filter);

    for (T pojo : coll) {
      results.add(pojo);
    }
    return results;
  }

  /**
   * Update a single document by its _id. The provided {@code update} should be
   * a valid MongoDB update document (for example, an Updates.combine(...) or
   * a simple Updates.set(...)). Returns the number of modified documents
   * (0 or 1).
   */
  public boolean updateById(String id, Bson update) {
    if (id == null || id.isBlank()) return false;

    Bson filter;
    if (ObjectId.isValid(id)) {
      filter = Filters.eq("_id", new ObjectId(id));
    } else {
      filter = Filters.eq("_id", id);
    }

    UpdateResult res = getCollection().updateOne(filter, update);
    long modified = res == null ? 0L : res.getModifiedCount();
    return modified > 0L;
  }

  /**
   * Delete a single document by its _id. Returns true if a document was deleted.
   */
  public boolean deleteById(String id) {
    if (id == null || id.isBlank()) return false;

    Bson filter;
    if (ObjectId.isValid(id)) {
      filter = Filters.eq("_id", new ObjectId(id));
    } else {
      filter = Filters.eq("_id", id);
    }

    DeleteResult res = getCollection().deleteOne(filter);
    long deleted = res == null ? 0L : res.getDeletedCount();
    return deleted > 0L;
  }

  public T create(T object) {
    if (object == null) return null;

    MongoCollection<T> collection = getCollection();
    collection.insertOne(object);
    return object;
  }

  

  private MongoCollection<T> getCollection() {
    MongoClient client = MongoClientProvider.getInstance().getOrCreateMongoClient();
    MongoCollection<T> collection = client.getDatabase(databaseName).getCollection(collectionName,
        mongoClass);
    return collection;
  }

  public Class<T> getMongoClass() {
    return mongoClass;
  }
}