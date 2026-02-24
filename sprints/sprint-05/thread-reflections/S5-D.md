# S5-D Thread Reflection

## What Worked

1. Keeping `F-1` strictly additive prevented overlap with active parser/generation threads.
2. Isolating LLM concerns into `autoapply/llm` made it easy to test fallback semantics without touching existing runtime flows.
3. Contract-first documentation clarified phase boundaries (`F-1` vs `F-2/F-3`) and reduced coupling risk.

## What Was Tricky

1. Worktree path permissions required escalated writes for Sprint artifact files.
2. Capturing deterministic fallback as explicit reason codes required deciding stable names early.

## Follow-Ups for Next Threads

1. `F-2`: connect `resume_parse` prompt contract to parse normalization pipeline behind feature-gated execution.
2. `F-3`: connect `resume_generate` prompt contract to generation candidate output while preserving claims-map and compliance gates.
3. Add observability fields (provider, prompt version, fallback reason) once runtime logging/diagnostics workstream is active.
