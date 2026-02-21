# -----------------------------------------------------------------------------
# ECS Task Execution Role (shared by both services)
# Allows ECS to pull images, write logs, and read secrets
# -----------------------------------------------------------------------------

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Name = "${local.name_prefix}-ecs-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_base" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "execution_secrets" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [aws_secretsmanager_secret.openai_api_key.arn]
  }
}

resource "aws_iam_role_policy" "execution_secrets" {
  name   = "${local.name_prefix}-execution-secrets"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.execution_secrets.json
}

# -----------------------------------------------------------------------------
# Crawler Task Role
# S3: ListBucket + PutObject/GetObject on crawls/*
# -----------------------------------------------------------------------------

resource "aws_iam_role" "crawler_task" {
  name               = "${local.name_prefix}-crawler-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Name = "${local.name_prefix}-crawler-task-role"
  }
}

data "aws_iam_policy_document" "crawler_s3" {
  statement {
    sid     = "ListBucket"
    actions = ["s3:ListBucket"]
    resources = [aws_s3_bucket.data.arn]
  }

  statement {
    sid = "CrawlsReadWrite"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.data.arn}/crawls/*"]
  }
}

resource "aws_iam_role_policy" "crawler_s3" {
  name   = "${local.name_prefix}-crawler-s3"
  role   = aws_iam_role.crawler_task.id
  policy = data.aws_iam_policy_document.crawler_s3.json
}

# -----------------------------------------------------------------------------
# Analyzer Task Role
# S3: ListBucket + GetObject on crawls/* + PutObject/GetObject on analyzer/*
# -----------------------------------------------------------------------------

resource "aws_iam_role" "analyzer_task" {
  name               = "${local.name_prefix}-analyzer-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Name = "${local.name_prefix}-analyzer-task-role"
  }
}

data "aws_iam_policy_document" "analyzer_s3" {
  statement {
    sid     = "ListBucket"
    actions = ["s3:ListBucket"]
    resources = [aws_s3_bucket.data.arn]
  }

  statement {
    sid     = "ReadCrawls"
    actions = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.data.arn}/crawls/*"]
  }

  statement {
    sid = "AnalyzerReadWrite"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.data.arn}/analyzer/*"]
  }
}

resource "aws_iam_role_policy" "analyzer_s3" {
  name   = "${local.name_prefix}-analyzer-s3"
  role   = aws_iam_role.analyzer_task.id
  policy = data.aws_iam_policy_document.analyzer_s3.json
}
