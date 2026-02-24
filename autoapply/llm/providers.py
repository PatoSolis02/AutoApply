from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from autoapply.llm.config import LlmConfig


@dataclass(frozen=True)
class PromptMessage:
    role: str
    content: str


@dataclass(frozen=True)
class PromptSpec:
    workflow: str
    version: str


@dataclass(frozen=True)
class LlmRequest:
    prompt: PromptSpec
    messages: tuple[PromptMessage, ...]
    model: str
    temperature: float
    timeout_seconds: float


@dataclass(frozen=True)
class LlmResponse:
    text: str
    provider: str
    model: str
    prompt_version: str
    raw: dict[str, Any] | None = None


class LlmProviderError(RuntimeError):
    """Raised when the provider call fails."""


class LlmProviderClient(Protocol):
    provider: str

    def complete(self, request: LlmRequest) -> LlmResponse:
        raise NotImplementedError


ProviderFactory = Callable[[LlmConfig], LlmProviderClient]


class ProviderRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}

    def register(self, provider: str, factory: ProviderFactory) -> None:
        self._factories[provider] = factory

    def create(self, config: LlmConfig) -> LlmProviderClient | None:
        factory = self._factories.get(config.provider)
        if factory is None:
            return None
        return factory(config)


class UnimplementedProviderClient:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    def complete(self, request: LlmRequest) -> LlmResponse:
        raise LlmProviderError(
            f"provider '{self.provider}' is configured but runtime calls are not implemented in F-1"
        )


def default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("openai", lambda _config: UnimplementedProviderClient("openai"))
    registry.register("anthropic", lambda _config: UnimplementedProviderClient("anthropic"))
    return registry
