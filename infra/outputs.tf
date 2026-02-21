# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "analyzer_url" {
  description = "URL of the analyzer service (ALB DNS name)"
  value       = "http://${aws_lb.analyzer.dns_name}"
}

output "crawler_ecr_repository_url" {
  description = "ECR repository URL for the crawler image"
  value       = aws_ecr_repository.crawler.repository_url
}

output "analyzer_ecr_repository_url" {
  description = "ECR repository URL for the analyzer image"
  value       = aws_ecr_repository.analyzer.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "s3_bucket_name" {
  description = "Name of the shared S3 bucket"
  value       = aws_s3_bucket.data.id
}

output "crawler_log_group" {
  description = "CloudWatch log group for the crawler"
  value       = aws_cloudwatch_log_group.crawler.name
}

output "analyzer_log_group" {
  description = "CloudWatch log group for the analyzer"
  value       = aws_cloudwatch_log_group.analyzer.name
}

output "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret in Secrets Manager"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}
