# -----------------------------------------------------------------------------
# REST API Task Definition
# -----------------------------------------------------------------------------

resource "aws_ecs_task_definition" "rest" {
  family                   = "${local.name_prefix}-rest"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.rest_cpu
  memory                   = var.rest_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.rest_task.arn

  container_definitions = jsonencode([
    {
      name      = "rest"
      image     = local.rest_ecr_image_uri
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "PORT", value = "8080" },
        { name = "CRAWLER_API_URL", value = "http://crawler.falcon-iq.local:8080" },
        { name = "ECS_CLUSTER_NAME", value = aws_ecs_cluster.main.name },
        { name = "ECS_CRAWLER_SERVICE", value = aws_ecs_service.crawler.name },
        { name = "ECS_ANALYZER_SERVICE", value = aws_ecs_service.analyzer.name },
        { name = "AWS_REGION", value = var.aws_region },
      ]

      secrets = [
        {
          name      = "MONGO_URI"
          valueFrom = aws_secretsmanager_secret.mongo_uri.arn
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.openai_api_key.arn
        }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8080/api/health/live || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 5
        startPeriod = 120
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.rest.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "rest"
        }
      }
    }
  ])

  tags = {
    Name = "${local.name_prefix}-rest-task"
  }
}

# -----------------------------------------------------------------------------
# REST API ECS Service
# Public-facing via ALB (path-based routing: /api/*)
# -----------------------------------------------------------------------------

resource "aws_ecs_service" "rest" {
  name            = "${local.name_prefix}-rest"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.rest.arn
  desired_count   = var.rest_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.rest.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.rest.arn
    container_name   = "rest"
    container_port   = 8080
  }

  depends_on = [
    aws_lb_listener_rule.rest_api,
  ]

  tags = {
    Name = "${local.name_prefix}-rest-service"
  }
}
