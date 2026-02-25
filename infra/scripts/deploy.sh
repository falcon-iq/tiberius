#!/usr/bin/env bash
# =============================================================================
# Falcon IQ Full Deployment Script
# =============================================================================
# Automates: terraform apply -> docker build -> docker push -> verify
#
# Prerequisites:
#   - AWS CLI configured (aws configure)
#   - Terraform installed
#   - Docker running
#   - terraform.tfvars configured
#   - TF_VAR_openai_api_key set
#
# Usage:
#   ./scripts/deploy.sh              # Full deploy
#   ./scripts/deploy.sh --skip-infra # Skip terraform, just build & push images
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
APPS_DIR="$INFRA_DIR/../apps"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
info()  { echo -e "${BLUE}[→]${NC} $1"; }

SKIP_INFRA=false
for arg in "$@"; do
  case $arg in
    --skip-infra) SKIP_INFRA=true ;;
  esac
done

# -------------------------------------------------------
# Preflight checks
# -------------------------------------------------------
info "Running preflight checks..."

if ! command -v aws &>/dev/null; then
  error "AWS CLI not found. Install: brew install awscli"
  exit 1
fi

if ! command -v terraform &>/dev/null; then
  error "Terraform not found. Install: brew install terraform"
  exit 1
fi

if ! command -v docker &>/dev/null; then
  error "Docker not found. Install Docker Desktop."
  exit 1
fi

if ! docker info &>/dev/null; then
  error "Docker daemon not running. Start Docker Desktop."
  exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
  error "AWS credentials not configured. Run 'aws configure' first."
  exit 1
}
log "AWS Account: $AWS_ACCOUNT_ID"

if [ -z "${TF_VAR_openai_api_key:-}" ]; then
  error "TF_VAR_openai_api_key not set."
  echo "  Run: export TF_VAR_openai_api_key=\"sk-...\""
  exit 1
fi
log "OpenAI API key is set"

if [ -z "${TF_VAR_mongo_uri:-}" ]; then
  error "TF_VAR_mongo_uri not set."
  echo "  Run: export TF_VAR_mongo_uri=\"mongodb+srv://user:pass@cluster.mongodb.net/dbname\""
  exit 1
fi
log "MongoDB URI is set"

cd "$INFRA_DIR"

if [ ! -f terraform.tfvars ]; then
  error "terraform.tfvars not found."
  echo "  Run: cp terraform.tfvars.example terraform.tfvars"
  echo "  Then edit it with your values."
  exit 1
fi
log "terraform.tfvars found"

# Read region from tfvars
AWS_REGION=$(grep -E '^aws_region\s*=' terraform.tfvars | sed 's/.*=\s*"\(.*\)"/\1/' || echo "us-east-1")
log "AWS Region: $AWS_REGION"

# -------------------------------------------------------
# Step 1: Terraform
# -------------------------------------------------------
if [ "$SKIP_INFRA" = false ]; then
  echo ""
  info "Step 1/5: Deploying infrastructure with Terraform..."
  echo ""

  terraform init -input=false

  echo ""
  info "Planning changes..."
  terraform plan -input=false -out=tfplan

  echo ""
  warn "Review the plan above. Continue with apply?"
  read -rp "  Type 'yes' to apply: " confirm
  if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    rm -f tfplan
    exit 0
  fi

  terraform apply -input=false tfplan
  rm -f tfplan
  log "Infrastructure deployed"
else
  info "Skipping infrastructure (--skip-infra)"
fi

# -------------------------------------------------------
# Step 2: Build Docker images
# -------------------------------------------------------
echo ""
info "Step 2/5: Building Docker images..."

export AWS_ACCOUNT_ID
export AWS_REGION

info "Building crawler..."
cd "$APPS_DIR/falcon-iq-crawler"
./build.sh latest
log "Crawler image built"

info "Building analyzer..."
cd "$APPS_DIR/falcon-iq-analyzer"
./build.sh latest
log "Analyzer image built"

info "Building REST API..."
cd "$APPS_DIR/falcon-iq-rest"
./build.sh latest
log "REST API image built"

# -------------------------------------------------------
# Step 3: Push to ECR
# -------------------------------------------------------
echo ""
info "Step 3/5: Pushing images to ECR..."

cd "$APPS_DIR/falcon-iq-crawler"
./build.sh latest push
log "Crawler image pushed"

cd "$APPS_DIR/falcon-iq-analyzer"
./build.sh latest push
log "Analyzer image pushed"

cd "$APPS_DIR/falcon-iq-rest"
./build.sh latest push
log "REST API image pushed"

# -------------------------------------------------------
# Step 4: Wait for services to stabilize
# -------------------------------------------------------
echo ""
info "Step 4/5: Waiting for ECS services to stabilize..."

cd "$INFRA_DIR"
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
CRAWLER_SERVICE="${CLUSTER_NAME%-cluster}-crawler"
ANALYZER_SERVICE="${CLUSTER_NAME%-cluster}-analyzer"
REST_SERVICE="${CLUSTER_NAME%-cluster}-rest"

info "Forcing new deployment to pick up latest images..."
aws ecs update-service --cluster "$CLUSTER_NAME" --service "$CRAWLER_SERVICE" \
  --force-new-deployment --no-cli-pager >/dev/null
aws ecs update-service --cluster "$CLUSTER_NAME" --service "$ANALYZER_SERVICE" \
  --force-new-deployment --no-cli-pager >/dev/null
aws ecs update-service --cluster "$CLUSTER_NAME" --service "$REST_SERVICE" \
  --force-new-deployment --no-cli-pager >/dev/null

info "Waiting for crawler to reach steady state (this may take a few minutes)..."
aws ecs wait services-stable --cluster "$CLUSTER_NAME" --services "$CRAWLER_SERVICE" 2>/dev/null || {
  warn "Crawler service did not stabilize within timeout. Check logs: make logs-crawler"
}

info "Waiting for analyzer to reach steady state..."
aws ecs wait services-stable --cluster "$CLUSTER_NAME" --services "$ANALYZER_SERVICE" 2>/dev/null || {
  warn "Analyzer service did not stabilize within timeout. Check logs: make logs-analyzer"
}

info "Waiting for REST API to reach steady state..."
aws ecs wait services-stable --cluster "$CLUSTER_NAME" --services "$REST_SERVICE" 2>/dev/null || {
  warn "REST API service did not stabilize within timeout. Check logs: make logs-rest"
}

# -------------------------------------------------------
# Done
# -------------------------------------------------------
echo ""
echo "=========================================="
log "Deployment complete!"
echo "=========================================="
echo ""
ANALYZER_URL=$(terraform output -raw analyzer_url)
REST_API_URL=$(terraform output -raw rest_api_url)
echo -e "  Analyzer URL:  ${GREEN}${ANALYZER_URL}${NC}"
echo -e "  REST API URL:  ${GREEN}${REST_API_URL}${NC}"
echo -e "  Health check:  ${GREEN}${ANALYZER_URL}/health${NC}"
echo -e "  REST health:   ${GREEN}${REST_API_URL}/health${NC}"
echo ""
echo "  Useful commands:"
echo "    make status          - Check service health"
echo "    make logs-crawler    - Tail crawler logs"
echo "    make logs-analyzer   - Tail analyzer logs"
echo "    make logs-rest       - Tail REST API logs"
echo "    make redeploy        - Force new deployment"
echo "    make destroy         - Tear down everything"
echo ""
