from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from autoapply.llm.config import LlmConfig
from autoapply.llm.providers import (
    LlmProviderClient,
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
        deterministic_reason = self._resolve_deterministic_reason()
        if deterministic_reason is not None:
            return self._deterministic_result(
                reason=deterministic_reason,
                prompt_version=prompt_version,
                deterministic_fn=deterministic_fn,
            )

        client = self._provider_registry.create(self._config)
        if client is None:
            return self._deterministic_result(
                reason="provider_unavailable",
                prompt_version=prompt_version,
                deterministic_fn=deterministic_fn,
            )

        request = LlmRequest(
            prompt=PromptSpec(workflow=workflow, version=prompt_version),
            messages=tuple(messages),
            model=self._config.model or "",
            temperature=temperature,
            timeout_seconds=self._config.timeout_seconds,
        )
        response, fallback_reason = self._complete_request(client=client, request=request)
        if fallback_reason is not None:
            return self._deterministic_result(
                reason=fallback_reason,
                prompt_version=prompt_version,
                deterministic_fn=deterministic_fn,
            )
        if response is None:
            return self._deterministic_result(
                reason="provider_exception",
                prompt_version=prompt_version,
                deterministic_fn=deterministic_fn,
            )

        try:
            transformed = llm_transform(response)
        except Exception:
            return self._deterministic_result(
                reason="provider_exception",
                prompt_version=prompt_version,
                deterministic_fn=deterministic_fn,
            )

        return LlmExecutionResult(
            value=transformed,
            metadata=LlmExecutionMetadata(
                mode="llm",
                reason="llm_success",
                provider=self._config.provider,
                model=self._config.model,
                prompt_version=prompt_version,
            ),
        )

    def _resolve_deterministic_reason(self) -> str | None:
        if not self._config.enabled:
            return "llm_disabled"
        if self._config.provider == "none":
            return "provider_not_selected"
        if not self._config.provider_ready():
            return "provider_not_configured"
        return None

    def _complete_request(
        self,
        *,
        client: LlmProviderClient,
        request: LlmRequest,
    ) -> tuple[LlmResponse | None, str | None]:
        try:
            return client.complete(request), None
        except LlmProviderError:
            return None, "provider_error"
        except Exception:
            return None, "provider_exception"

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
