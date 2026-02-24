# S6-C Thread Reflection

## What Worked

1. Reusing the existing `LlmRuntime` fallback contract kept parser normalization integration small and predictable.
2. Adding transform-error fallback in runtime closed a real reliability gap for invalid LLM JSON responses.
3. Field-level change tracing made normalization decisions inspectable without changing core profile contract shape.

## What Was Tricky

1. Balancing normalization flexibility with safety required conservative merge rules to avoid fabricated or structurally unstable profile edits.
2. Parser unit tests needed explicit injected LLM runtimes to keep enabled/disabled behavior deterministic under test.

## Risks / Residual Gaps

1. Current trace evidence is heuristic (substring matching) and not a full provenance engine.
2. Real provider quality behavior is still gated on future provider client implementation and prompt tuning.
3. Conservative list merge strategy may under-correct badly segmented resumes; this is intentional for contract safety.

## Follow-Ups

1. Add provider-backed eval fixtures for `resume_parse` normalization quality scoring.
2. Introduce stricter typed schema validation for LLM response payloads prior to merge.
3. Consider optional persisted normalization audit snapshots when observability/export workstreams are integrated.
