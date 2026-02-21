# =============================================================================
# Falcon IQ Infrastructure Makefile
# =============================================================================
# Usage:
#   make setup        - First-time setup (init + copy tfvars)
#   make plan         - Preview infrastructure changes
#   make deploy       - Deploy infrastructure
#   make build-push   - Build and push Docker images to ECR
#   make status       - Check ECS service health
#   make logs-crawler - Tail crawler logs
#   make logs-analyzer - Tail analyzer logs
#   make redeploy     - Force new ECS deployment (after image push)
#   make destroy      - Tear down all infrastructure
#   make outputs      - Show Terraform outputs
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Derived values
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
AWS_REGION := $(shell terraform output -raw 2>/dev/null || echo "us-east-1")
CLUSTER_NAME := $(shell terraform output -raw ecs_cluster_name 2>/dev/null)
APPS_DIR := ../apps

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

.PHONY: help
help: ## Show this help
	@echo ""
	@echo "Falcon IQ Infrastructure Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'
	@echo ""

# -----------------------------------------------------------------------------
# Setup & Init
# -----------------------------------------------------------------------------

.PHONY: setup
setup: ## First-time setup: init Terraform and create tfvars from example
	@echo "$(GREEN)Initializing Terraform...$(NC)"
	terraform init
	@if [ ! -f terraform.tfvars ]; then \
		cp terraform.tfvars.example terraform.tfvars; \
		echo "$(YELLOW)Created terraform.tfvars from example. Edit it with your values.$(NC)"; \
		echo "$(YELLOW)Then set: export TF_VAR_openai_api_key=\"sk-...\"$(NC)"; \
	else \
		echo "terraform.tfvars already exists, skipping copy."; \
	fi

.PHONY: init
init: ## Re-initialize Terraform (after backend/provider changes)
	terraform init

# -----------------------------------------------------------------------------
# Plan & Deploy
# -----------------------------------------------------------------------------

.PHONY: validate
validate: ## Validate Terraform configuration
	terraform validate

.PHONY: plan
plan: ## Preview infrastructure changes
	terraform plan

.PHONY: deploy
deploy: ## Deploy infrastructure (terraform apply)
	@echo "$(GREEN)Deploying infrastructure...$(NC)"
	terraform apply
	@echo ""
	@echo "$(GREEN)Infrastructure deployed. Next: make build-push$(NC)"

.PHONY: outputs
outputs: ## Show all Terraform outputs
	terraform output

# -----------------------------------------------------------------------------
# Docker Build & Push
# -----------------------------------------------------------------------------

.PHONY: check-aws
check-aws:
	@if [ -z "$(AWS_ACCOUNT_ID)" ]; then \
		echo "$(RED)Error: AWS credentials not configured. Run 'aws configure' first.$(NC)"; \
		exit 1; \
	fi
	@echo "AWS Account: $(AWS_ACCOUNT_ID)"

.PHONY: build-push
build-push: check-aws build-push-crawler build-push-analyzer ## Build and push both Docker images to ECR
	@echo ""
	@echo "$(GREEN)Both images pushed. Run 'make redeploy' to update ECS services.$(NC)"

.PHONY: build-push-crawler
build-push-crawler: check-aws ## Build and push crawler image
	@echo "$(GREEN)Building and pushing crawler...$(NC)"
	cd $(APPS_DIR)/falcon-iq-crawler && \
		AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID) \
		AWS_REGION=$(shell terraform output -raw 2>/dev/null | grep -v "^$$" || echo "us-east-1") \
		./build.sh latest push

.PHONY: build-push-analyzer
build-push-analyzer: check-aws ## Build and push analyzer image
	@echo "$(GREEN)Building and pushing analyzer...$(NC)"
	cd $(APPS_DIR)/falcon-iq-analyzer && \
		AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID) \
		AWS_REGION=$(shell terraform output -raw 2>/dev/null | grep -v "^$$" || echo "us-east-1") \
		./build.sh latest push

# -----------------------------------------------------------------------------
# ECS Operations
# -----------------------------------------------------------------------------

.PHONY: status
status: ## Check ECS service health and running tasks
	@echo "$(GREEN)ECS Service Status:$(NC)"
	@aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(CLUSTER_NAME:%-cluster=%-crawler) $(CLUSTER_NAME:%-cluster=%-analyzer) \
		--query 'services[].{Service:serviceName,Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
		--output table 2>/dev/null || echo "$(RED)Could not fetch status. Is infrastructure deployed?$(NC)"

.PHONY: redeploy
redeploy: redeploy-crawler redeploy-analyzer ## Force new deployment of both ECS services
	@echo "$(GREEN)Both services redeploying. Run 'make status' to monitor.$(NC)"

.PHONY: redeploy-crawler
redeploy-crawler: ## Force new deployment of crawler service
	@echo "$(GREEN)Redeploying crawler...$(NC)"
	@aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(CLUSTER_NAME:%-cluster=%-crawler) \
		--force-new-deployment \
		--query 'service.{Service:serviceName,Status:status}' \
		--output table

.PHONY: redeploy-analyzer
redeploy-analyzer: ## Force new deployment of analyzer service
	@echo "$(GREEN)Redeploying analyzer...$(NC)"
	@aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(CLUSTER_NAME:%-cluster=%-analyzer) \
		--force-new-deployment \
		--query 'service.{Service:serviceName,Status:status}' \
		--output table

# -----------------------------------------------------------------------------
# Logs
# -----------------------------------------------------------------------------

.PHONY: logs-crawler
logs-crawler: ## Tail crawler CloudWatch logs
	aws logs tail $(shell terraform output -raw crawler_log_group) --follow

.PHONY: logs-analyzer
logs-analyzer: ## Tail analyzer CloudWatch logs
	aws logs tail $(shell terraform output -raw analyzer_log_group) --follow

# -----------------------------------------------------------------------------
# Teardown
# -----------------------------------------------------------------------------

.PHONY: destroy
destroy: ## Destroy all infrastructure (WARNING: irreversible)
	@echo "$(RED)This will destroy ALL infrastructure and data.$(NC)"
	terraform destroy
