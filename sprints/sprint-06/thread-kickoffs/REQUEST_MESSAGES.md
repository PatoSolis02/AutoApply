# Sprint 06 Thread Kickoff Messages

Copy/paste each block as the first message in a separate thread.

## Thread A (AUT-13): Contract hardening

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/architecture/SAFETY_COMPLIANCE.md, and sprints/sprint-06/PLAN.md.

You own Sprint 06 Thread A for Linear issue AUT-13: Contract mismatch and fallback hardening.

Create/reuse branch: codex/s6-a-contract-fallback
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_a_contract_fallback

Scope:
- Implement robust handling for supported endpoint/response envelope variants.
- Harden fallback behavior and error surfaces for mismatch cases.
- Add regression tests for known contract drift patterns.

Out of scope:
- UI redesign
- LLM generation feature work

Deliverables:
- Handoff: sprints/sprint-06/handoffs/S6-A.md
- Reflection: sprints/sprint-06/thread-reflections/S6-A.md
- Include commit hash, tests run, assumptions/risks, contract notes.
```

## Thread B (AUT-11): Workflow smoke tests

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, and sprints/sprint-06/PLAN.md.

You own Sprint 06 Thread B for Linear issue AUT-11: End-to-end workflow smoke tests in CI.

Create/reuse branch: codex/s6-b-e2e-smoke
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_b_e2e_smoke

Scope:
- Add deterministic smoke scenarios for capture -> generate -> review -> approve -> audit.
- Wire smoke checks into CI workflows.
- Ensure failures identify workflow stage clearly.

Out of scope:
- Contract behavior changes
- Parser algorithm refactors

Deliverables:
- Handoff: sprints/sprint-06/handoffs/S6-B.md
- Reflection: sprints/sprint-06/thread-reflections/S6-B.md
- Include commit hash, tests run, assumptions/risks.
```

## Thread C (AUT-12): LLM parsing normalization

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/architecture/SAFETY_COMPLIANCE.md, and sprints/sprint-06/PLAN.md.

You own Sprint 06 Thread C for Linear issue AUT-12: LLM-assisted resume parsing normalization.

Create/reuse branch: codex/s6-c-llm-parse-normalization
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_c_llm_parse_normalization

Scope:
- Implement LLM-assisted normalization for parsed resume fields.
- Preserve traceability and deterministic fallback behavior.
- Add tests for LLM-enabled and LLM-disabled paths.

Out of scope:
- Full LLM-based resume generation feature (AUT-15)

Deliverables:
- Handoff: sprints/sprint-06/handoffs/S6-C.md
- Reflection: sprints/sprint-06/thread-reflections/S6-C.md
- Include commit hash, tests run, assumptions/risks, prompt/model contract notes.
```

## Thread D (AUT-14): Observability improvements

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, and sprints/sprint-06/PLAN.md.

You own Sprint 06 Thread D for Linear issue AUT-14: Runtime and API observability improvements.

Create/reuse branch: codex/s6-d-observability
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_d_observability

Scope:
- Add structured logs and correlation/request IDs for key flows.
- Improve diagnostics for common failure classes.
- Keep behavior and contracts stable.

Out of scope:
- External monitoring platform rollout
- Unrelated refactor sweeps

Deliverables:
- Handoff: sprints/sprint-06/handoffs/S6-D.md
- Reflection: sprints/sprint-06/thread-reflections/S6-D.md
- Include commit hash, tests run, assumptions/risks.
```

## Completion Signal

When all sprint threads are done, send:

`All Sprint 6 handoffs and retrospectives ready. Integrate from codex/integration.`
