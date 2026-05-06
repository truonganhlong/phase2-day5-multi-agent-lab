"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError

logger = logging.getLogger(__name__)


def _enable_langsmith_if_configured() -> bool:
    """If LANGSMITH_API_KEY is set, configure env so the tracer activates automatically."""

    settings = get_settings()
    if not settings.langsmith_api_key:
        return False
    # Force-set so values survive even if .env wasn't loaded into os.environ.
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    return True


def flush_langsmith() -> None:
    """Block until queued LangSmith traces are uploaded."""

    try:
        from langsmith import Client

        Client().flush()
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("LangSmith flush failed: %s", exc)


_PRICE_TABLE_USD_PER_1K = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},
}


def _estimate_cost(model: str, input_tokens: int | None, output_tokens: int | None) -> float | None:
    if input_tokens is None or output_tokens is None:
        return None
    price = _PRICE_TABLE_USD_PER_1K.get(model)
    if price is None:
        return None
    return (input_tokens / 1000) * price["input"] + (output_tokens / 1000) * price["output"]


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    model: str | None = None


class LLMClient:
    """Provider-agnostic LLM client backed by OpenAI."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise AgentExecutionError(
                "OPENAI_API_KEY is not set; populate .env before running LLM-backed agents."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AgentExecutionError(
                "openai package is not installed. Install with `pip install openai`."
            ) from exc

        raw_client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.timeout_seconds,
        )
        if _enable_langsmith_if_configured():
            try:
                from langsmith.wrappers import wrap_openai

                raw_client = wrap_openai(raw_client)
                logger.info(
                    "LangSmith tracing enabled (project=%s)", settings.langsmith_project
                )
            except Exception as exc:
                logger.warning("Failed to enable LangSmith tracing: %s", exc)
        self._client = raw_client
        self._model = model or settings.openai_model
        self._temperature = temperature
        self._max_tokens = max_tokens

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with retries and usage accounting."""

        logger.debug("LLM call model=%s temperature=%s", self._model, self._temperature)
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        choice = response.choices[0]
        content = (choice.message.content or "").strip()
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        output_tokens = getattr(usage, "completion_tokens", None) if usage else None
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=_estimate_cost(self._model, input_tokens, output_tokens),
            model=self._model,
        )
