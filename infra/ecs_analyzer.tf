# -----------------------------------------------------------------------------
# Analyzer Task Definition
# -----------------------------------------------------------------------------

resource "aws_ecs_task_definition" "analyzer" {
  family                   = "${local.name_prefix}-analyzer"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.analyzer_cpu
  memory                   = var.analyzer_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.analyzer_task.arn

  container_definitions = jsonencode([
    {
      name      = "analyzer"
      image     = local.analyzer_ecr_image_uri
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "WEB_ANALYZER_STORAGE_TYPE", value = "s3" },
        { name = "WEB_ANALYZER_S3_BUCKET_NAME", value = var.s3_bucket_name },
        { name = "WEB_ANALYZER_AWS_REGION", value = var.aws_region },
        { name = "WEB_ANALYZER_CRAWLER_API_URL", value = local.crawler_internal_url },
        { name = "WEB_ANALYZER_LLM_PROVIDER", value = var.analyzer_llm_provider },
        { name = "WEB_ANALYZER_OPENAI_MODEL", value = var.analyzer_openai_model },
        { name = "WEB_ANALYZER_HOST", value = "0.0.0.0" },
        { name = "WEB_ANALYZER_PORT", value = "8000" },
        { name = "WEB_ANALYZER_MAX_CONCURRENCY", value = "3" },
      ]

      secrets = [
        {
          name      = "WEB_ANALYZER_OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.openai_api_key.arn
        }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 30
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.analyzer.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "analyzer"
        }
      }
    }
  ])

  tags = {
    Name = "${local.name_prefix}-analyzer-task"
  }
}

# -----------------------------------------------------------------------------
# Analyzer ECS Service
# Public-facing via ALB
# -----------------------------------------------------------------------------

resource "aws_ecs_service" "analyzer" {
  name            = "${local.name_prefix}-analyzer"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.analyzer.arn
  desired_count   = var.analyzer_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.analyzer.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.analyzer.arn
    container_name   = "analyzer"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener.http,
    aws_ecs_service.crawler,
  ]

  tags = {
    Name = "${local.name_prefix}-analyzer-service"
  }
}
