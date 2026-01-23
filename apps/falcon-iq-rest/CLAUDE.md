# Falcon IQ REST API Context

Essential context for working with the Falcon IQ REST API. For monorepo-wide context, see `/CLAUDE.md`.

---

## Tech Stack

- **Java 21**
- **Jersey 3.1.11** (JAX-RS implementation)
- **Jetty 12.0.27** (embedded server for standalone, or external container)
- **Maven** (build tool)
- **Jackson** (JSON serialization)

---

## Project Structure

```
falcon-iq-rest/
├── src/
│   ├── main/
│   │   ├── java/com/example/fiq/
│   │   │   ├── generic/          # Generic CRUD services
│   │   │   └── ...               # Application code
│   │   └── webapp/
│   │       └── WEB-INF/
│   │           └── web.xml       # Servlet configuration
│   └── test/java/                # Test files
├── pom.xml                       # Maven configuration
├── README.md                     # Build & deployment instructions
└── DOCKER.md                     # Docker setup
```

---

## Essential Commands

### Development (Standalone JAR)

```bash
# Build and run standalone JAR (includes embedded Jetty)
mvn clean package -Pstandalone -DskipTests
java -jar target/falcon-iq-rest-1.0.0-standalone.jar
```

Application runs on `http://localhost:8080/api/`

**Example endpoints:**
- Hello: `http://localhost:8080/api/hello`
- Metadata: `http://localhost:8080/api/generic-bean-api/metadata/OKR_STATUS`

### Build WAR for Production

```bash
# Build WAR (default, for servlet containers)
mvn clean package

# Output: target/falcon-iq-rest-1.0.0.war
```

### Testing

```bash
mvn test                 # Run tests
mvn clean verify         # Run tests with integration tests
```

### Using Nx Commands

```bash
nx run falcon-iq-rest:build       # Build WAR
nx run falcon-iq-rest:serve       # Run standalone JAR
nx run falcon-iq-rest:test        # Run tests
```

---

## Deployment Options

### Option 1: Standalone JAR (Development/Testing)

**Best for:** Local development, quick testing

```bash
mvn clean package -Pstandalone -DskipTests
java -jar target/falcon-iq-rest-1.0.0-standalone.jar
```

**Includes:** Embedded Jetty server, all dependencies bundled

### Option 2: WAR with External Jetty (Production-like)

**Best for:** Production deployment, servlet containers

1. **Install Jetty:**
   ```bash
   brew install jetty
   ```

2. **Setup Jetty base:**
   ```bash
   mkdir -p ~/jetty-base/webapps
   cd ~/jetty-base
   java -jar /opt/homebrew/opt/jetty/libexec/start.jar \
     --add-modules=server,http,ee10-deploy,ee10-webapp
   ```

3. **Build and deploy WAR:**
   ```bash
   mvn clean package -DskipTests
   cp target/falcon-iq-rest-1.0.0.war ~/jetty-base/webapps/falcon-iq-rest.war
   ```

4. **Start Jetty:**
   ```bash
   cd ~/jetty-base
   java -jar /opt/homebrew/opt/jetty/libexec/start.jar &
   ```

5. **Stop Jetty:**
   ```bash
   pkill -f jetty
   ```

### Option 3: Docker (See DOCKER.md)

```bash
docker build -t falcon-iq-rest .
docker run -d -p 8080:8080 --name falcon-iq falcon-iq-rest
```

---

## Maven Configuration

### Packaging

- **Default:** WAR (for servlet containers)
- **Standalone profile:** Shaded JAR with embedded Jetty

### Key Properties

```xml
<properties>
  <maven.compiler.release>21</maven.compiler.release>
  <jersey.version>3.1.11</jersey.version>
  <jetty.version>12.0.27</jetty.version>
</properties>
```

### Profiles

- **Default:** Builds WAR without Jetty
- **`standalone`:** Builds shaded JAR with embedded Jetty and all dependencies

```bash
mvn clean package                    # WAR
mvn clean package -Pstandalone       # Standalone JAR
```

---

## Project Conventions

### Package Structure

```
com.example.fiq/
├── generic/              # Generic CRUD framework
│   ├── GenericMongoCRUDService
│   ├── GenericBeanMetadata
│   ├── FilterOperator
│   └── ...
└── ...                  # Application-specific code
```

### REST Endpoints

Base URL: `http://localhost:8080/api/`

**Example patterns:**
- `GET /api/hello` - Health check
- `GET /api/generic-bean-api/metadata/{type}` - Metadata endpoint
- Custom endpoints defined in JAX-RS resources

### Adding New Endpoints

1. Create JAX-RS resource class:
   ```java
   @Path("/my-resource")
   public class MyResource {
       @GET
       @Produces(MediaType.APPLICATION_JSON)
       public Response get() {
           return Response.ok("data").build();
       }
   }
   ```

2. Ensure class is in scanned package (defined in `web.xml`)

3. Test locally with standalone JAR

---

## Code Organization Standards

Follow monorepo standards (see `/CLAUDE.md`):
- Tests in `src/test/java/`
- Use conventional package structure
- Maven follows standard directory layout

---

## Common Gotchas

1. **WAR vs JAR:** WAR doesn't include Jetty (use external server), standalone JAR includes embedded Jetty
2. **Servlet API conflicts:** `jakarta.servlet-api` is marked as `provided` in main dependencies, included in standalone profile
3. **Port conflicts:** Default port is 8080, change if needed
4. **Build failures:** Run `mvn clean` first if encountering issues
5. **Test failures:** Use `-DskipTests` for quick builds during development

---

## Health Monitoring

**Endpoint:** `http://localhost:8080/api/health`

**Docker health check:**
```bash
docker inspect --format='{{json .State.Health}}' falcon-iq | jq
```

---

## Development Workflow

1. **Make code changes** in `src/main/java/`
2. **Run tests:** `mvn test`
3. **Quick test with standalone JAR:**
   ```bash
   mvn clean package -Pstandalone -DskipTests
   java -jar target/falcon-iq-rest-1.0.0-standalone.jar
   ```
4. **Test endpoints** with curl or browser
5. **Commit with conventional commits** (use `npm run commit` from root)

---

## Integration with Electron App

The Electron app (`falcon-iq-electron-app`) can communicate with this REST API:

1. Start REST API: `nx run falcon-iq-rest:serve`
2. Start Electron app: `nx run falcon-iq-electron-app:dev`
3. Electron app calls REST endpoints via HTTP

---

## Quick Reference

| Task | Command |
|------|---------|
| Run locally | `mvn clean package -Pstandalone -DskipTests && java -jar target/falcon-iq-rest-1.0.0-standalone.jar` |
| Build WAR | `mvn clean package` |
| Run tests | `mvn test` |
| Build Docker image | `docker build -t falcon-iq-rest .` |
| Stop Jetty | `pkill -f jetty` |

---

*For Docker deployment details, see `DOCKER.md`. For monorepo context, see `/CLAUDE.md`.*
