from falcon_iq_analyzer.config import Settings
from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.ollama_client import OllamaClient
from falcon_iq_analyzer.llm.openai_client import OpenAIClient


def create_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "openai":
        return OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            max_concurrency=settings.max_concurrency,
        )
    elif settings.llm_provider == "ollama":
        return OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            num_ctx=settings.ollama_num_ctx,
            max_concurrency=min(settings.max_concurrency, 2),
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
