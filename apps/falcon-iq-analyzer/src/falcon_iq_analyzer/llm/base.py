import json
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt and return the text response."""

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Send a prompt and return a parsed JSON response."""
        raw = await self.complete(system_prompt, user_prompt)
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)
