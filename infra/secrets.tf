# -----------------------------------------------------------------------------
# Secrets Manager - OpenAI API Key
# -----------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "${local.name_prefix}/openai-api-key"
  description = "OpenAI API key for the analyzer service"

  tags = {
    Name = "${local.name_prefix}-openai-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

# -----------------------------------------------------------------------------
# Secrets Manager - MongoDB URI
# -----------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "mongo_uri" {
  name        = "${local.name_prefix}/mongo-uri"
  description = "MongoDB connection URI for the REST API service"

  tags = {
    Name = "${local.name_prefix}-mongo-uri"
  }
}

resource "aws_secretsmanager_secret_version" "mongo_uri" {
  secret_id     = aws_secretsmanager_secret.mongo_uri.id
  secret_string = var.mongo_uri
}
