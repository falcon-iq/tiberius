# Multi-stage build for Falcon IQ REST API
# Stage 1: Build the WAR file
FROM maven:3.9-eclipse-temurin-21 AS builder

# Set working directory
WORKDIR /app

# Copy pom.xml and source code
COPY pom.xml .
COPY src ./src

# Build the WAR file (skip tests for faster builds, enable in CI/CD)
RUN mvn clean package -DskipTests

# Stage 2: Runtime with Tomcat 10.x + JDK 21 (Temurin)
FROM tomcat:10.1-jdk21-temurin

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Remove default webapps for security and cleaner deployment
RUN rm -rf /usr/local/tomcat/webapps/*

# Copy the WAR file as ROOT.war to serve at '/'
COPY --from=builder /app/target/falcon-iq-rest-1.0.0.war /usr/local/tomcat/webapps/ROOT.war

# Create a non-root user for security (AWS Fargate best practice)
RUN groupadd -r falcon && useradd -r -g falcon falcon
RUN chown -R falcon:falcon /usr/local/tomcat

# AWS Fargate optimized JVM settings
# - Use container-aware heap sizing
# - Enable G1GC for better performance in containerized environments
# - Optimize for Fargate's CPU/memory allocation
ENV CATALINA_OPTS="-Dfile.encoding=UTF-8 \
    -XX:+UseG1GC \
    -XX:+UseContainerSupport \
    -XX:MaxRAMPercentage=75.0 \
    -XX:InitialRAMPercentage=50.0 \
    -Djava.security.egd=file:/dev/./urandom \
    -Dspring.profiles.active=docker"

# Set MongoDB configuration via environment variables for Fargate
ENV MONGO_URI=""
ENV MONGO_USERNAME=""
ENV MONGO_PASSWORD=""
ENV MONGO_HOST=""

# Expose port 8080 (Tomcat default)
EXPOSE 8080

# Health check for AWS Fargate/ECS service health monitoring
# Points to a health endpoint that should be added to your application
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Switch to non-root user
USER falcon

# Start Tomcat
CMD ["catalina.sh", "run"]