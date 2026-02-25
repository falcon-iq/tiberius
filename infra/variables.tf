# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "falcon-iq"
}

variable "environment" {
  description = "Deployment environment (must be full name per project conventions)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production. Abbreviations are not allowed."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

# -----------------------------------------------------------------------------
# Crawler
# -----------------------------------------------------------------------------

variable "crawler_image_tag" {
  description = "Docker image tag for the crawler service"
  type        = string
  default     = "latest"
}

variable "crawler_cpu" {
  description = "CPU units for crawler task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "crawler_memory" {
  description = "Memory (MiB) for crawler task"
  type        = number
  default     = 1024
}

variable "crawler_desired_count" {
  description = "Number of crawler tasks to run"
  type        = number
  default     = 1
}

variable "crawler_max_concurrent_crawls" {
  description = "Maximum concurrent crawls per crawler instance"
  type        = number
  default     = 3
}

# -----------------------------------------------------------------------------
# Analyzer
# -----------------------------------------------------------------------------

variable "analyzer_image_tag" {
  description = "Docker image tag for the analyzer service"
  type        = string
  default     = "latest"
}

variable "analyzer_cpu" {
  description = "CPU units for analyzer task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "analyzer_memory" {
  description = "Memory (MiB) for analyzer task"
  type        = number
  default     = 2048
}

variable "analyzer_desired_count" {
  description = "Number of analyzer tasks to run"
  type        = number
  default     = 1
}

variable "analyzer_llm_provider" {
  description = "LLM provider for the analyzer (e.g., openai)"
  type        = string
  default     = "openai"
}

variable "analyzer_openai_model" {
  description = "OpenAI model name for the analyzer"
  type        = string
  default     = "gpt-4o-mini"
}

# -----------------------------------------------------------------------------
# REST API
# -----------------------------------------------------------------------------

variable "rest_image_tag" {
  description = "Docker image tag for the REST API service"
  type        = string
  default     = "latest"
}

variable "rest_cpu" {
  description = "CPU units for REST API task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "rest_memory" {
  description = "Memory (MiB) for REST API task"
  type        = number
  default     = 1024
}

variable "rest_desired_count" {
  description = "Number of REST API tasks to run"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# Secrets
# -----------------------------------------------------------------------------

variable "openai_api_key" {
  description = "OpenAI API key. Set via TF_VAR_openai_api_key env var rather than in tfvars."
  type        = string
  sensitive   = true
}

variable "mongo_uri" {
  description = "MongoDB connection URI. Set via TF_VAR_mongo_uri env var rather than in tfvars."
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------

variable "s3_bucket_name" {
  description = "Name for the shared S3 bucket (must be globally unique)"
  type        = string
}

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}
