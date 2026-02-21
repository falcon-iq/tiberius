# Falcon IQ AWS Infrastructure

Terraform-managed ECS Fargate deployment for the Falcon IQ Crawler and Analyzer services.

## Architecture

- **Crawler** (internal): ECS Fargate in private subnets, discovered via Cloud Map (`crawler.falcon-iq.local:8080`)
- **Analyzer** (public): ECS Fargate in private subnets, exposed via ALB on port 80
- Shared S3 bucket for crawled pages and analysis results
- OpenAI API key stored in Secrets Manager

## Prerequisites

- [Terraform](https://www.terraform.io/) >= 1.5
- [AWS CLI](https://aws.amazon.com/cli/) configured (`aws configure`)
- [Docker](https://www.docker.com/) + [buildx](https://github.com/docker/buildx) (for cross-platform builds)
- [Colima](https://github.com/abiosoft/colima) or Docker Desktop running

## First-Time Setup

```bash
cd infra

# 1. Initialize Terraform
terraform init

# 2. Create your variables file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values (s3_bucket_name must be globally unique)

# 3. Set the OpenAI API key (never put this in tfvars)
export TF_VAR_openai_api_key="sk-..."

# 4. Review and deploy infrastructure
terraform plan
terraform apply

# 5. Set AWS variables for Docker builds
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# 6. Build and push images
cd ../apps/falcon-iq-crawler
./build.sh latest push

cd ../apps/falcon-iq-analyzer
./build.sh latest push

# 7. Force ECS to pick up images
aws ecs update-service --cluster falcon-iq-development-cluster \
  --service falcon-iq-development-crawler --force-new-deployment --no-cli-pager
aws ecs update-service --cluster falcon-iq-development-cluster \
  --service falcon-iq-development-analyzer --force-new-deployment --no-cli-pager
```

## Build & Deploy (day-to-day)

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# Build & push
cd apps/falcon-iq-crawler && ./build.sh latest push
cd apps/falcon-iq-analyzer && ./build.sh latest push

# Deploy
aws ecs update-service --cluster falcon-iq-development-cluster \
  --service falcon-iq-development-crawler --force-new-deployment --no-cli-pager
aws ecs update-service --cluster falcon-iq-development-cluster \
  --service falcon-iq-development-analyzer --force-new-deployment --no-cli-pager
```

## Monitoring

```bash
# Service status
aws ecs describe-services \
  --cluster falcon-iq-development-cluster \
  --services falcon-iq-development-crawler falcon-iq-development-analyzer \
  --query 'services[].{name:serviceName,running:runningCount,desired:desiredCount}' \
  --output table

# Tail logs
aws logs tail /ecs/falcon-iq-development/crawler --follow
aws logs tail /ecs/falcon-iq-development/analyzer --follow

# Health check
curl $(cd infra && terraform output -raw analyzer_url)/health
```

## Makefile Commands

All operations are also available via `make` from the `infra/` directory:

| Command | Description |
|---|---|
| `make setup` | First-time setup (init + copy tfvars) |
| `make plan` | Preview infrastructure changes |
| `make deploy` | Deploy infrastructure (terraform apply) |
| `make build-push` | Build and push both Docker images |
| `make redeploy` | Force new ECS deployment |
| `make status` | Check ECS service health |
| `make logs-crawler` | Tail crawler logs |
| `make logs-analyzer` | Tail analyzer logs |
| `make outputs` | Show Terraform outputs |
| `make destroy` | Tear down all infrastructure |

## Teardown

```bash
cd infra
terraform destroy
```

## Cost Estimate (development)

| Resource | ~Monthly Cost |
|---|---|
| NAT Gateway | $32 |
| ALB | $16 |
| Fargate (crawler 0.25 vCPU) | $7 |
| Fargate (analyzer 1 vCPU) | $29 |
| CloudWatch Logs | $1-5 |
| S3 | < $1 |
| **Total** | **~$85-90/mo** |

Run `terraform destroy` when not in use to stop billing.
