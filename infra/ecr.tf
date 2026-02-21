# -----------------------------------------------------------------------------
# ECR Repositories
# Names match existing build.sh scripts (falcon-iq-crawler, falcon-iq-analyzer)
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "crawler" {
  name                 = "falcon-iq-crawler"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "falcon-iq-crawler"
  }
}

resource "aws_ecr_repository" "analyzer" {
  name                 = "falcon-iq-analyzer"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "falcon-iq-analyzer"
  }
}

# -----------------------------------------------------------------------------
# Lifecycle Policies - keep last 10 untagged images
# -----------------------------------------------------------------------------

resource "aws_ecr_lifecycle_policy" "crawler" {
  repository = aws_ecr_repository.crawler.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 untagged images"
        selection = {
          tagStatus   = "untagged"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "analyzer" {
  repository = aws_ecr_repository.analyzer.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 untagged images"
        selection = {
          tagStatus   = "untagged"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
