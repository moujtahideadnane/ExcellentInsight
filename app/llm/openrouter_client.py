import asyncio
import json
import re

import httpx
import structlog

from app.config import get_settings
from app.llm.client import LLMClient, LLMResponse
from app.utils.circuit_breaker import CircuitBreaker, with_timeout

settings = get_settings()
logger = structlog.get_logger()

# Global circuit breaker for LLM calls
# Opens after 5 consecutive failures, recovers after 60 seconds
_llm_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=Exception,
    name="openrouter_llm",
)


def repair_json(content: str) -> str:
    """Attempts to repair truncated JSON by closing brackets/braces."""
    content = content.strip()
    if not content:
        return "{}"

    # Remove trailing incomplete key/value or comma
    content = re.sub(r',?\s*["\w]*\s*:?\s*$', "", content)

    # Count open/close brackets
    braces = content.count("{") - content.count("}")
    brackets = content.count("[") - content.count("]")

    # Close them in reverse order
    repair = content
    # Look at simple stack-based approach for more complex nesting
    # For now, append closing characters
    if brackets > 0:
        repair += "]" * brackets
    if braces > 0:
        repair += "}" * braces

    try:
        json.loads(repair)
        return repair
    except Exception:
        # If still failing, try a more aggressive approach: find last '}' or ']'
        last_brace = content.rfind("}")
        last_bracket = content.rfind("]")
        last_pos = max(last_brace, last_bracket)
        if last_pos > 0:
            # Try to close from there
            sub_content = content[: last_pos + 1]
            # Check if it needs more closing (e.g. outer object)
            braces_sub = sub_content.count("{") - sub_content.count("}")
            brackets_sub = sub_content.count("[") - sub_content.count("]")
            sub_content += "]" * brackets_sub
            sub_content += "}" * braces_sub
            try:
                json.loads(sub_content)
                return sub_content
            except Exception:
                pass

    return content


class OpenRouterClient(LLMClient):
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        base = settings.OPENROUTER_BASE_URL.rstrip("/")
        if base.endswith("/chat/completions"):
            self.base_url = base
        else:
            self.base_url = f"{base}/chat/completions"
        self.model = settings.LLM_MODEL
        self.fallback_model = settings.LLM_FALLBACK_MODEL

    async def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Complete LLM request with circuit breaker and timeout protection.

        Raises:
            CircuitBreakerOpen: If circuit breaker is open due to previous failures
            TimeoutError: If request exceeds 30 second timeout
            Exception: Other errors from LLM API
        """
        # Use circuit breaker to prevent cascading failures
        return await _llm_circuit_breaker.call(self._complete_internal, prompt, system_prompt)

    @with_timeout(300.0)  # 30 second timeout for LLM calls
    async def _complete_internal(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Internal completion method with timeout protection."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://excellentinsight.ai",  # Optional
            "X-Title": "ExcellentInsight",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            "max_tokens": settings.LLM_MAX_TOKENS,
            "temperature": settings.LLM_TEMPERATURE,
            # Request JSON mode if possible or structured output
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
            max_retries = 3
            last_error = None

            for attempt in range(max_retries):
                try:
                    response = await client.post(self.base_url, headers=headers, json=payload)

                    if response.status_code in [503, 504, 429]:
                        wait_time = (attempt + 1) * 2
                        logger.warning(
                            f"OpenRouter busy/unavailable (HTTP {response.status_code}). Retrying in {wait_time}s...",
                            attempt=attempt + 1,
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})

                    parsed_json = None
                    try:
                        parsed_json = json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning("LLM response was not valid JSON, attempting repair", length=len(content))
                        repaired = repair_json(content)
                        try:
                            parsed_json = json.loads(repaired)
                            logger.info("JSON successfully repaired")
                        except Exception:
                            logger.error("JSON repair failed", content_preview=content[:100])

                    return LLMResponse(content=content, parsed_json=parsed_json, usage=usage)
                except httpx.HTTPStatusError as e:
                    last_error = e
                    logger.warning(f"OpenRouter status error (HTTP {e.response.status_code}) on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        # Try fallback model before giving up
                        logger.warning("Primary model failed status check, trying fallback model", error=str(e))
                        # ... (rest of fallback logic handled below)
                    else:
                        await asyncio.sleep((attempt + 1) * 2)
                        continue
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    last_error = e
                    logger.warning(f"OpenRouter connection/timeout error on attempt {attempt + 1}: {repr(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep((attempt + 1) * 2)
                        continue
                    else:
                        logger.error("OpenRouter max retries reached for connection errors")
                except Exception:
                    logger.exception("Unexpected error during OpenRouter call")
                    raise

            # If we reached here, it means we exhausted retries or want to try fallback
            if last_error:
                logger.warning("Attempting fallback model due to previous errors")
                try:
                    fallback_payload = payload.copy()
                    fallback_payload["model"] = self.fallback_model
                    response = await client.post(self.base_url, headers=headers, json=fallback_payload)
                    response.raise_for_status()
                    data = response.json()

                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})

                    parsed_json = None
                    try:
                        parsed_json = json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning("Fallback LLM response was not valid JSON, attempting repair")
                        repaired = repair_json(content)
                        try:
                            parsed_json = json.loads(repaired)
                            logger.info("Fallback JSON successfully repaired")
                        except Exception:
                            logger.error("Fallback JSON repair failed")

                    return LLMResponse(content=content, parsed_json=parsed_json, usage=usage)
                except Exception as fallback_error:
                    logger.error("Fallback model also failed", error=repr(fallback_error))
                    raise last_error from fallback_error

            raise RuntimeError("LLM API request failed after max retries")
