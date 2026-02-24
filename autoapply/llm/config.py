from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

LLM_PROVIDER_NONE = "none"
LLM_PROVIDER_OPENAI = "openai"
LLM_PROVIDER_ANTHROPIC = "anthropic"
_VALID_PROVIDERS = {
    LLM_PROVIDER_NONE,
    LLM_PROVIDER_OPENAI,
    LLM_PROVIDER_ANTHROPIC,
}
_TRUE_VALUES = {"1", "true", "yes", "on"}
_DEFAULT_MODELS = {
    LLM_PROVIDER_OPENAI: "gpt-4o-mini",
    LLM_PROVIDER_ANTHROPIC: "claude-3-5-haiku-latest",
}
_WORKFLOW_RESUME_GENERATE = "resume_generate"
_WORKFLOW_RESUME_PARSE = "resume_parse"


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def _parse_float(value: str | None, *, default: float) -> float:
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    if parsed <= 0:
        return default
    return parsed


@dataclass(frozen=True)
class LlmConfig:
    enabled: bool
    provider: str
    model: str | None
    api_key: str | None
    base_url: str | None
    timeout_seconds: float
    generate_prompt_version: str
    parse_prompt_version: str
    config_warnings: tuple[str, ...]

    def provider_ready(self) -> bool:
        if self.provider == LLM_PROVIDER_NONE:
            return False
        if not self.model:
            return False
        return bool(self.api_key)

    def prompt_version_for(self, workflow: str) -> str:
        if workflow == _WORKFLOW_RESUME_PARSE:
            return self.parse_prompt_version
        return self.generate_prompt_version


def load_llm_config(env: Mapping[str, str] | None = None) -> LlmConfig:
    source = os.environ if env is None else env
    warnings: list[str] = []

    enabled = _parse_bool(source.get("AUTOAPPLY_LLM_ENABLED"), default=False)
    provider_raw = (source.get("AUTOAPPLY_LLM_PROVIDER") or LLM_PROVIDER_NONE).strip().lower()
    provider = provider_raw
    if provider not in _VALID_PROVIDERS:
        warnings.append(f"unsupported provider '{provider_raw}' configured; using '{LLM_PROVIDER_NONE}'")
        provider = LLM_PROVIDER_NONE

    explicit_model = (source.get("AUTOAPPLY_LLM_MODEL") or "").strip()
    if explicit_model:
        model: str | None = explicit_model
    else:
        model = _DEFAULT_MODELS.get(provider)

    api_key = _resolve_api_key(provider=provider, env=source)
    base_url = (source.get("AUTOAPPLY_LLM_BASE_URL") or "").strip() or None
    timeout_seconds = _parse_float(source.get("AUTOAPPLY_LLM_TIMEOUT_SECONDS"), default=15.0)
    generate_prompt_version = (source.get("AUTOAPPLY_LLM_GENERATE_PROMPT_VERSION") or "resume_generate.v1").strip()
    parse_prompt_version = (source.get("AUTOAPPLY_LLM_PARSE_PROMPT_VERSION") or "resume_parse.v1").strip()

    if enabled and provider == LLM_PROVIDER_NONE:
        warnings.append("llm is enabled but no provider is configured; deterministic fallback will be used")

    if enabled and provider != LLM_PROVIDER_NONE and not api_key:
        warnings.append("llm provider selected without API key; deterministic fallback will be used")

    return LlmConfig(
        enabled=enabled,
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        generate_prompt_version=generate_prompt_version,
        parse_prompt_version=parse_prompt_version,
        config_warnings=tuple(warnings),
    )


def _resolve_api_key(provider: str, env: Mapping[str, str]) -> str | None:
    if provider == LLM_PROVIDER_OPENAI:
        return _resolve_env_value(env, "AUTOAPPLY_OPENAI_API_KEY", "OPENAI_API_KEY")
    if provider == LLM_PROVIDER_ANTHROPIC:
        return _resolve_env_value(env, "AUTOAPPLY_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY")
    return None


def _resolve_env_value(env: Mapping[str, str], *keys: str) -> str | None:
    for key in keys:
        value = (env.get(key) or "").strip()
        if value:
            return value
    return None
