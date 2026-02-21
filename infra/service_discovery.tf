# -----------------------------------------------------------------------------
# Cloud Map Private DNS Namespace
# -----------------------------------------------------------------------------

resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "falcon-iq.local"
  description = "Private DNS namespace for Falcon IQ service discovery"
  vpc         = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-dns-namespace"
  }
}

# -----------------------------------------------------------------------------
# Crawler Service Discovery Entry
# Registers crawler task IPs as crawler.falcon-iq.local
# -----------------------------------------------------------------------------

resource "aws_service_discovery_service" "crawler" {
  name = "crawler"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = {
    Name = "${local.name_prefix}-crawler-discovery"
  }
}
