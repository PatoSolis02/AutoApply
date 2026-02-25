from __future__ import annotations

import unittest

from autoapply.llm import (
    LLM_PROVIDER_NONE,
    LLM_PROVIDER_OPENAI,
    LlmProviderError,
    LlmResponse,
    LlmRuntime,
    PromptMessage,
    ProviderRegistry,
    load_llm_config,
)


class LlmConfigTests(unittest.TestCase):
    def test_load_defaults_are_safe_and_disabled(self) -> None:
        config = load_llm_config({})
        self.assertFalse(config.enabled)
        self.assertEqual(config.provider, LLM_PROVIDER_NONE)
        self.assertEqual(config.generate_prompt_version, "resume_generate.v1")
        self.assertEqual(config.parse_prompt_version, "resume_parse.v1")

    def test_load_openai_provider_with_env_values(self) -> None:
        config = load_llm_config(
            {
                "AUTOAPPLY_LLM_ENABLED": "true",
                "AUTOAPPLY_LLM_PROVIDER": "openai",
                "AUTOAPPLY_LLM_MODEL": "gpt-test",
                "AUTOAPPLY_OPENAI_API_KEY": "secret",
                "AUTOAPPLY_LLM_TIMEOUT_SECONDS": "22",
                "AUTOAPPLY_LLM_GENERATE_PROMPT_VERSION": "resume_generate.v2",
            }
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.provider, LLM_PROVIDER_OPENAI)
        self.assertEqual(config.model, "gpt-test")
        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.timeout_seconds, 22.0)
        self.assertEqual(config.generate_prompt_version, "resume_generate.v2")
        self.assertTrue(config.provider_ready())

    def test_invalid_provider_falls_back_to_none_with_warning(self) -> None:
        config = load_llm_config(
            {
                "AUTOAPPLY_LLM_ENABLED": "1",
                "AUTOAPPLY_LLM_PROVIDER": "mystery",
            }
        )
        self.assertEqual(config.provider, LLM_PROVIDER_NONE)
        self.assertTrue(config.config_warnings)
        self.assertIn("unsupported provider", config.config_warnings[0])


class LlmRuntimeFallbackTests(unittest.TestCase):
    def test_runtime_uses_deterministic_when_disabled(self) -> None:
        runtime = LlmRuntime(load_llm_config({}))
        deterministic_called = False

        def _deterministic() -> dict[str, str]:
            nonlocal deterministic_called
            deterministic_called = True
            return {"source": "deterministic"}

        result = runtime.run_with_fallback(
            workflow="resume_generate",
            messages=[PromptMessage(role="user", content="test")],
            llm_transform=lambda response: {"source": response.text},
            deterministic_fn=_deterministic,
        )
        self.assertTrue(deterministic_called)
        self.assertEqual(result.value["source"], "deterministic")
        self.assertEqual(result.metadata.mode, "deterministic")
        self.assertEqual(result.metadata.reason, "llm_disabled")

    def test_runtime_uses_deterministic_when_provider_not_configured(self) -> None:
        config = load_llm_config(
            {
                "AUTOAPPLY_LLM_ENABLED": "1",
                "AUTOAPPLY_LLM_PROVIDER": "openai",
            }
        )
        runtime = LlmRuntime(config)
        result = runtime.run_with_fallback(
            workflow="resume_generate",
            messages=[PromptMessage(role="user", content="test")],
            llm_transform=lambda response: {"source": response.text},
            deterministic_fn=lambda: {"source": "deterministic"},
        )
        self.assertEqual(result.value["source"], "deterministic")
        self.assertEqual(result.metadata.reason, "provider_not_configured")

    def test_runtime_uses_deterministic_when_provider_registry_has_no_client(self) -> None:
        runtime = LlmRuntime(
            load_llm_config(
                {
                    "AUTOAPPLY_LLM_ENABLED": "true",
                    "AUTOAPPLY_LLM_PROVIDER": "openai",
                    "AUTOAPPLY_OPENAI_API_KEY": "secret",
                }
            ),
            provider_registry=ProviderRegistry(),
        )
        result = runtime.run_with_fallback(
            workflow="resume_generate",
            messages=[PromptMessage(role="user", content="test")],
            llm_transform=lambda response: {"source": response.text},
            deterministic_fn=lambda: {"source": "deterministic"},
        )
        self.assertEqual(result.value["source"], "deterministic")
        self.assertEqual(result.metadata.reason, "provider_unavailable")

    def test_runtime_returns_llm_output_when_provider_succeeds(self) -> None:
        class _Client:
            provider = "openai"

            def complete(self, request):
                return LlmResponse(
                    text="llm-value",
                    provider="openai",
                    model=request.model,
                    prompt_version=request.prompt.version,
                )

        registry = ProviderRegistry()
        registry.register("openai", lambda _config: _Client())
        runtime = LlmRuntime(
            load_llm_config(
                {
                    "AUTOAPPLY_LLM_ENABLED": "true",
                    "AUTOAPPLY_LLM_PROVIDER": "openai",
                    "AUTOAPPLY_OPENAI_API_KEY": "secret",
                }
            ),
            provider_registry=registry,
        )

        deterministic_called = False

        def _deterministic() -> dict[str, str]:
            nonlocal deterministic_called
            deterministic_called = True
            return {"source": "deterministic"}

        result = runtime.run_with_fallback(
            workflow="resume_generate",
            messages=[PromptMessage(role="user", content="test")],
            llm_transform=lambda response: {"source": response.text},
            deterministic_fn=_deterministic,
        )
        self.assertFalse(deterministic_called)
        self.assertEqual(result.value["source"], "llm-value")
        self.assertEqual(result.metadata.mode, "llm")
        self.assertEqual(result.metadata.reason, "llm_success")

    def test_runtime_falls_back_when_provider_raises(self) -> None:
        class _Client:
            provider = "openai"

            def complete(self, request):
                raise LlmProviderError("upstream failed")

        registry = ProviderRegistry()
        registry.register("openai", lambda _config: _Client())
        runtime = LlmRuntime(
            load_llm_config(
                {
                    "AUTOAPPLY_LLM_ENABLED": "true",
                    "AUTOAPPLY_LLM_PROVIDER": "openai",
                    "AUTOAPPLY_OPENAI_API_KEY": "secret",
                }
            ),
            provider_registry=registry,
        )
        result = runtime.run_with_fallback(
            workflow="resume_generate",
            messages=[PromptMessage(role="user", content="test")],
            llm_transform=lambda response: {"source": response.text},
            deterministic_fn=lambda: {"source": "deterministic"},
        )
        self.assertEqual(result.value["source"], "deterministic")
        self.assertEqual(result.metadata.mode, "deterministic")
        self.assertEqual(result.metadata.reason, "provider_error")

    def test_runtime_falls_back_when_transform_raises(self) -> None:
        class _Client:
            provider = "openai"

            def complete(self, request):
                return LlmResponse(
                    text="not-json",
                    provider="openai",
                    model=request.model,
                    prompt_version=request.prompt.version,
                )

        registry = ProviderRegistry()
        registry.register("openai", lambda _config: _Client())
        runtime = LlmRuntime(
            load_llm_config(
                {
                    "AUTOAPPLY_LLM_ENABLED": "true",
                    "AUTOAPPLY_LLM_PROVIDER": "openai",
                    "AUTOAPPLY_OPENAI_API_KEY": "secret",
                }
            ),
            provider_registry=registry,
        )
        result = runtime.run_with_fallback(
            workflow="resume_generate",
            messages=[PromptMessage(role="user", content="test")],
            llm_transform=lambda _response: (_ for _ in ()).throw(ValueError("bad transform")),
            deterministic_fn=lambda: {"source": "deterministic"},
        )
        self.assertEqual(result.value["source"], "deterministic")
        self.assertEqual(result.metadata.mode, "deterministic")
        self.assertEqual(result.metadata.reason, "provider_exception")


if __name__ == "__main__":
    unittest.main()
