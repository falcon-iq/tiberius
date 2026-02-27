# -----------------------------------------------------------------------------
# Crawler Task Definition
# -----------------------------------------------------------------------------

resource "aws_ecs_task_definition" "crawler" {
  family                   = "${local.name_prefix}-crawler"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.crawler_cpu
  memory                   = var.crawler_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.crawler_task.arn

  container_definitions = jsonencode([
    {
      name      = "crawler"
      image     = local.crawler_ecr_image_uri
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "STORAGE_TYPE", value = "s3" },
        { name = "S3_BUCKET_NAME", value = var.s3_bucket_name },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "PORT", value = "8080" },
        { name = "MAX_CONCURRENT_CRAWLS", value = tostring(var.crawler_max_concurrent_crawls) },
        { name = "ANALYZER_API_URL", value = "http://${aws_lb.analyzer.dns_name}" },
      ]

      secrets = [
        {
          name      = "MONGO_URI"
          valueFrom = aws_secretsmanager_secret.mongo_uri.arn
        }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8080/api/health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 30
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.crawler.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "crawler"
        }
      }
    }
  ])

  tags = {
    Name = "${local.name_prefix}-crawler-task"
  }
}

# -----------------------------------------------------------------------------
# Crawler ECS Service
# Internal only - discovered via Cloud Map (crawler.falcon-iq.local:8080)
# -----------------------------------------------------------------------------

resource "aws_ecs_service" "crawler" {
  name            = "${local.name_prefix}-crawler"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.crawler.arn
  desired_count   = var.crawler_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.crawler.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.crawler.arn
  }

  tags = {
    Name = "${local.name_prefix}-crawler-service"
  }
}
