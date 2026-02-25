# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "crawler" {
  name              = "/ecs/${local.name_prefix}/crawler"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-crawler-logs"
  }
}

resource "aws_cloudwatch_log_group" "analyzer" {
  name              = "/ecs/${local.name_prefix}/analyzer"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-analyzer-logs"
  }
}

resource "aws_cloudwatch_log_group" "rest" {
  name              = "/ecs/${local.name_prefix}/rest"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-rest-logs"
  }
}
