# Multi-stage build for Falcon IQ Crawler

# Stage 1: Build the fat JAR
FROM maven:3.9-eclipse-temurin-21 AS builder

WORKDIR /app

COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Runtime with JRE 21
FROM eclipse-temurin:21-jre

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/falcon-iq-crawler-1.0.0.jar app.jar

# Create non-root user (AWS Fargate best practice)
RUN groupadd -r falcon && useradd -r -g falcon falcon
RUN mkdir -p /app/crawled_pages && chown -R falcon:falcon /app

# JVM settings optimized for containers
ENV JAVA_OPTS="-XX:+UseG1GC -XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:InitialRAMPercentage=50.0"

# Default to S3 storage in container (override for local dev)
ENV STORAGE_TYPE=s3
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

USER falcon

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
