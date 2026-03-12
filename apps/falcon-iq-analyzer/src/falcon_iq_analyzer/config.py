from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider: "openai" or "ollama"
    llm_provider: str = "openai"

    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    ollama_num_ctx: int = 32768

    # CORS
    cors_origins: list[str] = ["*"]

    # General
    max_concurrency: int = 10
    max_clean_text_chars: int = 4000
    host: str = "0.0.0.0"
    port: int = 8000

    # Crawler API
    crawler_api_url: str = "http://localhost:8080"

    # MongoDB (for progress reporting)
    mongo_uri: str = ""

    # Storage — report output (where analysis results & benchmark reports are saved)
    storage_type: str = "local"  # "local" or "s3" (or R2 via s3-compatible endpoint)
    s3_bucket_name: str = ""
    aws_region: str = "us-east-1"
    results_dir: str = "results"

    # Storage — crawl input (where the crawler saved HTML pages)
    crawl_storage_type: str = "local"  # "local" or "s3"
    crawled_sites_dir: str = "../falcon-iq-crawler/crawled_pages"

    # Cloudflare R2 (S3-compatible) — when set, boto3 uses R2 endpoint instead of AWS S3
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""

    model_config = {
        "env_prefix": "WEB_ANALYZER_",
        "env_file": ".env",
    }


settings = Settings()
