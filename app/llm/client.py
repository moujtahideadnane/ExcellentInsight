from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    usage: Dict[str, Any] = {}


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        pass
