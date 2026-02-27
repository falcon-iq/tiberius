locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  crawler_ecr_image_uri  = "${local.account_id}.dkr.ecr.${local.region}.amazonaws.com/falcon-iq-crawler:${var.crawler_image_tag}"
  analyzer_ecr_image_uri = "${local.account_id}.dkr.ecr.${local.region}.amazonaws.com/falcon-iq-analyzer:${var.analyzer_image_tag}"
  rest_ecr_image_uri     = "${local.account_id}.dkr.ecr.${local.region}.amazonaws.com/falcon-iq-rest:${var.rest_image_tag}"

  crawler_internal_url  = "http://crawler.falcon-iq.local:8080"
  analyzer_internal_url = "http://analyzer.falcon-iq.local:8000"
}
