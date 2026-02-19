import asyncio
import json
import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from falcon_iq_analyzer.llm.base import LLMClient

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
        num_ctx: int = 32768,
        max_concurrency: int = 2,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._num_ctx = num_ctx
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=300.0)

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
    )
    async def _call(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        async with self._semaphore:
            payload: dict = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"num_ctx": self._num_ctx, "temperature": 0.2},
            }
            if json_mode:
                payload["format"] = "json"
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        return await self._call(system_prompt, user_prompt, json_mode=False)

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        raw = await self._call(system_prompt, user_prompt, json_mode=True)
        return json.loads(raw)
