# LLM Foundation Contract (F-1)

Status: additive foundation only (no parser/generator replacement in this phase)

## Goals

1. Define a provider/config abstraction that is safe by default.
2. Define prompt/model version contracts for parsing and generation workflows.
3. Enforce deterministic fallback when LLM runtime cannot be used.

## Runtime Safety Baseline

1. LLM runtime is disabled by default (`AUTOAPPLY_LLM_ENABLED=false`).
2. If runtime is disabled, unconfigured, or provider calls fail, deterministic logic must execute.
3. Deterministic fallback must preserve existing behavior and compliance gates.

Fallback reason codes:

- `llm_disabled`
- `provider_not_selected`
- `provider_not_configured`
- `provider_unavailable`
- `provider_error`
- `provider_exception`

## Provider Config Contract

Environment variables:

- `AUTOAPPLY_LLM_ENABLED` (`true|false`, default `false`)
- `AUTOAPPLY_LLM_PROVIDER` (`none|openai|anthropic`, default `none`)
- `AUTOAPPLY_LLM_MODEL` (optional; provider default used when omitted)
- `AUTOAPPLY_LLM_TIMEOUT_SECONDS` (positive float, default `15.0`)
- `AUTOAPPLY_LLM_BASE_URL` (optional)
- `AUTOAPPLY_LLM_GENERATE_PROMPT_VERSION` (default `resume_generate.v1`)
- `AUTOAPPLY_LLM_PARSE_PROMPT_VERSION` (default `resume_parse.v1`)
- `AUTOAPPLY_OPENAI_API_KEY` or `OPENAI_API_KEY` (OpenAI)
- `AUTOAPPLY_ANTHROPIC_API_KEY` or `ANTHROPIC_API_KEY` (Anthropic)

## Prompt and Version Contract

Canonical prompt request shape:

```json
{
  "prompt": {
    "workflow": "resume_generate|resume_parse",
    "version": "string"
  },
  "model": "string",
  "messages": [
    {"role": "system|user|assistant", "content": "string"}
  ],
  "temperature": 0.0,
  "timeout_seconds": 15.0
}
```

Canonical provider response shape:

```json
{
  "text": "string",
  "provider": "string",
  "model": "string",
  "prompt_version": "string",
  "raw": "object|null"
}
```

## Phase Boundary

This contract introduces only configuration and runtime abstraction primitives.
Actual use of LLM output for parsing (`F-2`) or generation (`F-3`) is out of scope for `F-1`.
