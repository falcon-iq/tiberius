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

# -----------------------------------------------------------------------------
# Secrets Manager - Cloudflare R2 Credentials
# -----------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "r2_access_key_id" {
  name        = "${local.name_prefix}/r2-access-key-id"
  description = "Cloudflare R2 Access Key ID for the analyzer service"

  tags = {
    Name = "${local.name_prefix}-r2-access-key-id"
  }
}

resource "aws_secretsmanager_secret_version" "r2_access_key_id" {
  secret_id     = aws_secretsmanager_secret.r2_access_key_id.id
  secret_string = var.r2_access_key_id
}

resource "aws_secretsmanager_secret" "r2_secret_access_key" {
  name        = "${local.name_prefix}/r2-secret-access-key"
  description = "Cloudflare R2 Secret Access Key for the analyzer service"

  tags = {
    Name = "${local.name_prefix}-r2-secret-access-key"
  }
}

resource "aws_secretsmanager_secret_version" "r2_secret_access_key" {
  secret_id     = aws_secretsmanager_secret.r2_secret_access_key.id
  secret_string = var.r2_secret_access_key
}
