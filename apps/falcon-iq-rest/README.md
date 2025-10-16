How to build

Produce WAR (default): mvn clean package -> target/falcon-iq-rest-1.0.0.war

Produce standalone runnable JAR: mvn clean package -Pstandalone -> target/falcon-iq-rest-1.0.0-standalone.jar (shaded, contains dependencies, main=com.example.Main)

How to run

## Option 1: Standalone JAR (Development/Local)

Build and run the standalone JAR:
```bash
mvn clean package -Pstandalone -DskipTests
java -jar target/falcon-iq-rest-1.0.0-standalone.jar
```

The application will start on `http://localhost:8080/api/`

API Endpoints:
- Hello: http://localhost:8080/api/hello
- Metadata: http://localhost:8080/api/generic-bean-api/metadata/OKR_STATUS

## Option 2: Jetty Server (Production-like)

1. Install Jetty (macOS):
```bash
brew install jetty
```

2. Setup Jetty base directory:
```bash
mkdir -p ~/jetty-base/webapps
cd ~/jetty-base
java -jar /opt/homebrew/opt/jetty/libexec/start.jar --add-modules=server,http,ee10-deploy,ee10-webapp
```

3. Build and deploy WAR:
```bash
mvn clean package -DskipTests
cp target/falcon-iq-rest-1.0.0.war ~/jetty-base/webapps/falcon-iq-rest.war
```

4. Start Jetty server:
```bash
cd ~/jetty-base
java -jar /opt/homebrew/opt/jetty/libexec/start.jar &
```

5. Access the application:
- Base URL: http://localhost:8080/api/
- Hello: http://localhost:8080/api/hello
- Metadata: http://localhost:8080/api/generic-bean-api/metadata/OKR_STATUS

1. Stop Jetty server:
```bash
pkill -f jetty
```

Notes & suggestions

- The standalone JAR includes Jetty embedded; the WAR does not contain Jetty (good practice for servlet containers).
- For development, use the standalone JAR for quick testing.
- For production deployment, use the WAR file with a proper servlet container like Jetty or Tomcat.
- The WAR deployment requires web.xml configuration (located in src/main/webapp/WEB-INF/web.xml).
- If your standalone jar fails due to servlet API conflicts, jakarta.servlet-api is already marked as provided in main dependencies and included in the standalone profile.


How to generate DOCKER image

1. brew install docker colima
2. colima start - Colima automatically creates a VM, installs a Docker-compatible engine, and connects your docker CLI to it.
3. Build the image. Run this in the directory where your Dockerfile and pom.xml are located:
docker build -t falcon-iq-rest .
4. Run the container. Run Tomcat with your app:
docker run -d -p 8080:8080 --name falcon-iq falcon-iq-rest
5. Check container status
docker ps
6. Inspect logs
docker logs -f falcon-iq
7. Test the web app:
Visit in your browser: http://localhost:8080/
or curl it: curl -I http://localhost:8080/
8. Test the health endpoint
curl -v http://localhost:8080/api/health
9. Check Docker health status
After ~1 minute (because of the --start-period=60s), check:
docker inspect --format='{{json .State.Health}}' falcon-iq | jq
10. Clean up when done
docker stop falcon-iq
docker rm falcon-iq