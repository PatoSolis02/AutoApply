from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from autoapply.llm.config import LlmConfig
from autoapply.llm.providers import (
    LlmProviderError,
    LlmRequest,
    LlmResponse,
    PromptMessage,
    PromptSpec,
    ProviderRegistry,
    default_provider_registry,
)

T = TypeVar("T")


@dataclass(frozen=True)
class LlmExecutionMetadata:
    mode: str
    reason: str
    provider: str
    model: str | None
    prompt_version: str


@dataclass(frozen=True)
class LlmExecutionResult(Generic[T]):
    value: T
    metadata: LlmExecutionMetadata


class LlmRuntime:
    def __init__(
        self,
        config: LlmConfig,
        provider_registry: ProviderRegistry | None = None,
    ) -> None:
        self._config = config
        self._provider_registry = provider_registry or default_provider_registry()

    def run_with_fallback(
        self,
        *,
        workflow: str,
        messages: list[PromptMessage],
        llm_transform: Callable[[LlmResponse], T],
        deterministic_fn: Callable[[], T],
        temperature: float = 0.0,
    ) -> LlmExecutionResult[T]:
        prompt_version = self._config.prompt_version_for(workflow)
        fallback = lambda reason: self._deterministic_result(
            reason=reason,
            prompt_version=prompt_version,
            deterministic_fn=deterministic_fn,
        )

        if not self._config.enabled:
            return fallback("llm_disabled")
        if self._config.provider == "none":
            return fallback("provider_not_selected")
        if not self._config.provider_ready():
            return fallback("provider_not_configured")

        client = self._provider_registry.create(self._config)
        if client is None:
            return fallback("provider_unavailable")

        request = LlmRequest(
            prompt=PromptSpec(workflow=workflow, version=prompt_version),
            messages=tuple(messages),
            model=self._config.model or "",
            temperature=temperature,
            timeout_seconds=self._config.timeout_seconds,
        )
        try:
            response = client.complete(request)
        except LlmProviderError:
            return fallback("provider_error")
        except Exception:
            return fallback("provider_exception")

        return LlmExecutionResult(
            value=llm_transform(response),
            metadata=LlmExecutionMetadata(
                mode="llm",
                reason="llm_success",
                provider=self._config.provider,
                model=self._config.model,
                prompt_version=prompt_version,
            ),
        )

    def _deterministic_result(
        self,
        *,
        reason: str,
        prompt_version: str,
        deterministic_fn: Callable[[], T],
    ) -> LlmExecutionResult[T]:
        return LlmExecutionResult(
            value=deterministic_fn(),
            metadata=LlmExecutionMetadata(
                mode="deterministic",
                reason=reason,
                provider=self._config.provider,
                model=self._config.model,
                prompt_version=prompt_version,
            ),
        )
