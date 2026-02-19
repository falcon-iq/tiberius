import asyncio
import json
import logging

from openai import AsyncOpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from falcon_iq_analyzer.llm.base import LLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_concurrency: int = 10):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._semaphore = asyncio.Semaphore(max_concurrency)

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
    )
    async def _call(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        async with self._semaphore:
            kwargs: dict = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = await self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        return await self._call(system_prompt, user_prompt, json_mode=False)

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        raw = await self._call(system_prompt, user_prompt, json_mode=True)
        return json.loads(raw)
