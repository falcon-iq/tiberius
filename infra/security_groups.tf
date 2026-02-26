# -----------------------------------------------------------------------------
# ALB Security Group
# -----------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Allow HTTP/HTTPS inbound to ALB"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-alb-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_all" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# -----------------------------------------------------------------------------
# Analyzer Security Group
# -----------------------------------------------------------------------------

resource "aws_security_group" "analyzer" {
  name        = "${local.name_prefix}-analyzer-sg"
  description = "Allow inbound from ALB to analyzer"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-analyzer-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "analyzer_from_alb" {
  security_group_id            = aws_security_group.analyzer.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "analyzer_all" {
  security_group_id = aws_security_group.analyzer.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# -----------------------------------------------------------------------------
# Crawler Security Group
# -----------------------------------------------------------------------------

resource "aws_security_group" "crawler" {
  name        = "${local.name_prefix}-crawler-sg"
  description = "Allow inbound from analyzer to crawler"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-crawler-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "crawler_from_analyzer" {
  security_group_id            = aws_security_group.crawler.id
  referenced_security_group_id = aws_security_group.analyzer.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "crawler_from_rest" {
  security_group_id            = aws_security_group.crawler.id
  referenced_security_group_id = aws_security_group.rest.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "crawler_all" {
  security_group_id = aws_security_group.crawler.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# -----------------------------------------------------------------------------
# REST API Security Group
# -----------------------------------------------------------------------------

resource "aws_security_group" "rest" {
  name        = "${local.name_prefix}-rest-sg"
  description = "Allow inbound from ALB to REST API"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-rest-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "rest_from_alb" {
  security_group_id            = aws_security_group.rest.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "rest_all" {
  security_group_id = aws_security_group.rest.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}
