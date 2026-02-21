# -----------------------------------------------------------------------------
# Application Load Balancer (analyzer only)
# -----------------------------------------------------------------------------

resource "aws_lb" "analyzer" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "${local.name_prefix}-alb"
  }
}

# -----------------------------------------------------------------------------
# Target Group
# -----------------------------------------------------------------------------

resource "aws_lb_target_group" "analyzer" {
  name        = "${local.name_prefix}-anlz-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name = "${local.name_prefix}-analyzer-tg"
  }
}

# -----------------------------------------------------------------------------
# HTTP Listener
# For production, add an HTTPS listener with an ACM certificate and redirect
# HTTP to HTTPS.
# -----------------------------------------------------------------------------

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.analyzer.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.analyzer.arn
  }
}
