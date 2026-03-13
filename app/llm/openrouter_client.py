import asyncio
import json
import re
from typing import Dict

import httpx
import structlog

from app.config import get_settings
from app.llm.client import LLMClient, LLMResponse
from app.utils.circuit_breaker import CircuitBreaker, with_timeout

settings = get_settings()
logger = structlog.get_logger()

# Per-tenant circuit breakers for LLM calls to prevent cross-tenant failure cascades
# Opens after 5 consecutive failures, recovers after 60 seconds
_llm_circuit_breakers: Dict[str, CircuitBreaker] = {}


def _get_circuit_breaker(tenant_id: str = "default") -> CircuitBreaker:
    """Get or create circuit breaker for a specific tenant.

    Args:
        tenant_id: Organization/tenant identifier. Defaults to 'default' for backward compatibility.

    Returns:
        CircuitBreaker instance for the tenant
    """
    if tenant_id not in _llm_circuit_breakers:
        _llm_circuit_breakers[tenant_id] = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=Exception,
            name=f"openrouter_llm_{tenant_id}",
        )
    return _llm_circuit_breakers[tenant_id]


def repair_json(content: str, max_repairs: int = 20) -> str:
    """Attempts to repair truncated JSON by closing brackets/braces with security limits.

    Args:
        content: JSON string to repair
        max_repairs: Maximum number of brackets/braces to add (security limit)

    Returns:
        Repaired JSON string or original if repair fails
    """
    content = content.strip()
    if not content:
        return "{}"

    # Security: Reject extremely nested structures (potential DoS)
    if content.count("{") + content.count("[") > 1000:
        logger.warning("JSON repair rejected: too many nesting levels", count=content.count("{") + content.count("["))
        return content

    # Remove trailing incomplete key/value or comma
    content = re.sub(r',?\s*["\w]*\s*:?\s*$', "", content)

    # Count open/close brackets
    braces = content.count("{") - content.count("}")
    brackets = content.count("[") - content.count("]")

    # Security: Limit total repairs to prevent resource exhaustion
    total_repairs = braces + brackets
    if total_repairs > max_repairs:
        logger.warning(
            "JSON repair rejected: too many repairs needed",
            braces=braces,
            brackets=brackets,
            max_repairs=max_repairs,
        )
        return content

    # Close them in reverse order
    repair = content
    # Look at simple stack-based approach for more complex nesting
    # For now, append closing characters
    if brackets > 0:
        repair += "]" * brackets
    if braces > 0:
        repair += "}" * braces

    try:
        parsed = json.loads(repair)
        # Security: Validate structure after repair
        if not isinstance(parsed, dict):
            logger.warning("JSON repair produced non-dict result", type=type(parsed).__name__)
            return content
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

            # Security check on sub-content repairs
            if braces_sub + brackets_sub <= max_repairs:
                sub_content += "]" * brackets_sub
                sub_content += "}" * braces_sub
                try:
                    parsed = json.loads(sub_content)
                    # Security: Validate structure
                    if isinstance(parsed, dict):
                        return sub_content
                except Exception:
                    pass

    return content


class OpenRouterClient(LLMClient):
    def __init__(self, tenant_id: str = "default"):
        """Initialize OpenRouter client.

        Args:
            tenant_id: Organization/tenant identifier for circuit breaker isolation.
                      Defaults to 'default' for backward compatibility.
        """
        self.api_key = settings.OPENROUTER_API_KEY
        base = settings.OPENROUTER_BASE_URL.rstrip("/")
        if base.endswith("/chat/completions"):
            self.base_url = base
        else:
            self.base_url = f"{base}/chat/completions"
        self.model = settings.LLM_MODEL
        self.fallback_model = settings.LLM_FALLBACK_MODEL
        self.tenant_id = tenant_id

    async def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Complete LLM request with per-tenant circuit breaker and timeout protection.

        Raises:
            CircuitBreakerOpen: If circuit breaker is open due to previous failures
            TimeoutError: If request exceeds 540 second timeout
            Exception: Other errors from LLM API
        """
        # Use per-tenant circuit breaker to prevent cross-tenant failure cascades
        circuit_breaker = _get_circuit_breaker(self.tenant_id)
        return await circuit_breaker.call(self._complete_internal, prompt, system_prompt)

    @with_timeout(540.0)  # 9 minute timeout for LLM calls (aligned with httpx timeout below)
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

        async with httpx.AsyncClient(timeout=httpx.Timeout(540.0, connect=10.0)) as client:
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
