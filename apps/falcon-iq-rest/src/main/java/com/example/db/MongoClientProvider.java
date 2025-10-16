package com.example.db;

import com.mongodb.*;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import org.bson.UuidRepresentation;
import org.bson.codecs.configuration.CodecRegistry;
import org.bson.codecs.pojo.PojoCodecProvider;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Properties;
import java.io.InputStream;
import java.util.Optional;
import java.util.Map;
import static org.bson.codecs.configuration.CodecRegistries.*;

public final class MongoClientProvider implements AutoCloseable {
  private MongoClientProvider() {}

  private static final MongoClientProvider INSTANCE = new MongoClientProvider();
  private static final Object SHARED_LOCK = new Object();
  
  private static volatile MongoClient SHARED_CLIENT;

  public static MongoClientProvider getInstance() {
    return INSTANCE;
  }

  public MongoClient getOrCreateMongoClient() {
    if (SHARED_CLIENT == null) {
      synchronized (SHARED_LOCK) {
        if (SHARED_CLIENT == null) {
          // create via instance helper which reads resources.config/env
          SHARED_CLIENT = INSTANCE.createClient();
          // register a shutdown hook to close the client
          Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
              if (SHARED_CLIENT != null) {
                SHARED_CLIENT.close();
              }
            } catch (Exception ignored) {
            }
          }));
        }
      }
    }

    return SHARED_CLIENT;
  }
  /**
   * Create a MongoClient by reading configuration from classpath `resources.config`
   * and overriding with environment variables. Environment variables take precedence.
   * Supported envs / properties:
   *   - MONGO_URI / mongo.uri (full connection string)
   *   - MONGO_USERNAME / mongo.username
   *   - MONGO_PASSWORD / mongo.password
   *   - MONGO_HOST / mongo.host
   */
  private MongoClient createClient() {
    Properties props = new Properties();
    try (InputStream in = MongoClientProvider.class.getClassLoader().getResourceAsStream("resources.config")) {
      if (in != null) props.load(in);
    } catch (Exception ignored) {
      System.err.println("Warning: could not load resources.config from classpath" + ignored.getMessage());
    }

    Map<String, String> env = System.getenv();
    String uri = Optional.ofNullable(env.get("MONGO_URI")).orElse(props.getProperty("mongo.uri"));
    if (uri != null && !uri.isBlank()) {
      return createClientWithConnStr(uri);
    }

    String username = Optional.ofNullable(env.get("MONGO_USERNAME")).orElse(props.getProperty("mongo.username"));
    String password = Optional.ofNullable(env.get("MONGO_PASSWORD")).orElse(props.getProperty("mongo.password"));
    String host = Optional.ofNullable(env.get("MONGO_HOST")).orElse(props.getProperty("mongo.host"));

    if (username != null && host != null) {
      return createClient(username, password, host);
    }

    throw new IllegalStateException("No MongoDB configuration found in environment or resources.config");
  }

  /**
   * Keep the existing helper for username/password/host form.
   */
  private static MongoClient createClient(String username, String password, String host) {
    String encodedPassword = URLEncoder.encode(password == null ? "" : password, StandardCharsets.UTF_8);
    String connStr = String.format("mongodb+srv://%s:%s@%s/?retryWrites=true&w=majority", username, encodedPassword, host);
    return createClientWithConnStr(connStr);
  }

  private static MongoClient createClientWithConnStr(String connStr) {
    CodecRegistry pojoRegistry = fromRegistries(
        MongoClientSettings.getDefaultCodecRegistry(),
        fromProviders(PojoCodecProvider.builder().automatic(true).build())
    );

    MongoClientSettings settings = MongoClientSettings.builder()
        .applyConnectionString(new ConnectionString(connStr))
        .applicationName("fiq-web-service")
        .uuidRepresentation(UuidRepresentation.STANDARD)
        .codecRegistry(pojoRegistry)
        .retryReads(true)
        .retryWrites(true)
        // .compressorList(Arrays.asList(MongoCompressor.createZstdCompressor()))
        .applyToClusterSettings(b -> b.serverSelectionTimeout(5, java.util.concurrent.TimeUnit.SECONDS))
        .applyToSocketSettings(b -> b
            .connectTimeout(5, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(10, java.util.concurrent.TimeUnit.SECONDS))
        .applyToConnectionPoolSettings(b -> b
            .maxSize(100)                 // tune per workload
            .minSize(5)
            .maxConnecting(2)
            .maxConnectionIdleTime(5, java.util.concurrent.TimeUnit.MINUTES))
        // .addCommandListener(commandListener) // optional: observability TODO: enable
        // .serverApi(ServerApi.builder().version(ServerApiVersion.V1).build()) // if using Stable API
        .build();

    return MongoClients.create(settings);
  }

  public static MongoDatabase db(MongoClient client, String dbName) {
    return client.getDatabase(dbName); // inherits codec registry from client
  }

  @Override
  public void close() throws Exception {
    synchronized (SHARED_LOCK) {
      if (SHARED_CLIENT != null) {
        try {
          SHARED_CLIENT.close();
        } catch (Exception ignored) {
        } finally {
          SHARED_CLIENT = null;
        }
      }
    }
  }
}
