# Falcon IQ REST API - Docker & AWS Fargate Deployment Guide

## Overview

This guide covers Docker containerization and AWS Fargate deployment for the Falcon IQ REST API. The setup includes:

- Multi-stage Docker build optimized for production
- Health checks for AWS ECS/Fargate
- MongoDB connectivity via environment variables
- Security best practices (non-root user, minimal attack surface)

## Files Created

- `Dockerfile` - Multi-stage build with Tomcat 10.x + JDK 21
- `.dockerignore` - Build context optimization
- `docker-compose.yml` - Local development with MongoDB
- `docker/mongo-init.js` - MongoDB initialization script
- `build.sh` - Automated build and ECR push script
- `src/main/java/com/example/api/HealthCheckResource.java` - Health endpoints

## Quick Start

### Local Development

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Test the application:**
   ```bash
   # Health check
   curl http://localhost:8080/api/health
   
   # API endpoints
   curl http://localhost:8080/api/hello
   curl http://localhost:8080/api/generic-bean-api/metadata/OKR
   ```

### Production Build

1. **Build Docker image:**
   ```bash
   ./build.sh v1.0.0
   ```

2. **Push to AWS ECR:**
   ```bash
   export AWS_ACCOUNT_ID=123456789012
   export AWS_REGION=us-east-1
   ./build.sh v1.0.0 push
   ```

## AWS Fargate Deployment

### Prerequisites

1. **ECR Repository:**
   ```bash
   aws ecr create-repository --repository-name falcon-iq-rest --region us-east-1
   ```

2. **ECS Cluster:**
   ```bash
   aws ecs create-cluster --cluster-name falcon-iq-cluster
   ```

### Task Definition (JSON)

```json
{
  "family": "falcon-iq-rest",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "falcon-iq-rest",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/falcon-iq-rest:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MONGO_URI",
          "value": "mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/falcon-iq-rest",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8080/api/health || exit 1"
        ],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Environment Variables

Configure these in your Fargate task definition:

- `MONGO_URI` - Full MongoDB connection string
- `MONGO_USERNAME` - MongoDB username (alternative to URI)
- `MONGO_PASSWORD` - MongoDB password (alternative to URI)  
- `MONGO_HOST` - MongoDB host (alternative to URI)

### Resource Allocation

**Recommended Fargate configurations:**

- **Development:** 0.5 vCPU, 1GB RAM
- **Production:** 1-2 vCPU, 2-4GB RAM
- **High Load:** 4 vCPU, 8GB RAM

### Monitoring & Observability

1. **CloudWatch Logs:** Automatically configured in task definition
2. **Health Checks:** Three endpoints available:
   - `/api/health` - Full application health including MongoDB
   - `/api/ready` - Readiness check for load balancer
   - `/api/live` - Liveness check for container restart decisions

3. **Metrics:** Configure CloudWatch Container Insights for detailed metrics

## Security Considerations

- Container runs as non-root user (`falcon`)
- Minimal base image (Tomcat official image)
- No unnecessary packages installed
- MongoDB credentials via environment variables (use AWS Secrets Manager in production)
- Network policies should restrict access to MongoDB

## Troubleshooting

### Common Issues

1. **Health check failures:**
   - Check MongoDB connectivity
   - Verify environment variables
   - Check CloudWatch logs

2. **Out of Memory errors:**
   - Increase Fargate memory allocation
   - Tune `MaxRAMPercentage` in CATALINA_OPTS

3. **Slow startup:**
   - Increase health check `startPeriod`
   - Check MongoDB connection timeout settings

### Useful Commands

```bash
# Test Docker image locally
docker run -p 8080:8080 -e MONGO_URI="your-uri" falcon-iq-rest:latest

# Check container logs
aws logs tail /ecs/falcon-iq-rest --follow

# Describe Fargate service
aws ecs describe-services --cluster falcon-iq-cluster --services falcon-iq-service
```