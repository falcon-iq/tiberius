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

    # General
    max_concurrency: int = 10
    max_clean_text_chars: int = 4000
    host: str = "0.0.0.0"
    port: int = 8000

    # Crawler API
    crawler_api_url: str = "http://localhost:8080"

    # Storage
    storage_type: str = "local"  # "local" or "s3"
    s3_bucket_name: str = ""
    aws_region: str = "us-east-1"
    results_dir: str = "results"
    crawled_sites_dir: str = "crawled_sites"

    model_config = {
        "env_prefix": "WEB_ANALYZER_",
        "env_file": ".env",
    }


settings = Settings()
