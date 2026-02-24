# Sprint 07 Plan

Date: 2026-02-24
Mode: Parallel thread-batch (3 implementation threads)
Owner: Integration/Product (`codex/integration`)

## Sprint 07 Selection (from Linear)

Selected Linear issues:

1. `AUT-15` LLM-based tailored resume generation
2. `AUT-16` Technical debt cleanup in parser and runtime plumbing
3. `AUT-23` Test runtime resource warning cleanup

Tracking issues:

- `AUT-24` Integrate Sprint 07 handoffs into codex/integration
- `AUT-25` Sprint 07 recap and backlog rerank

## Why This Batch

- Highest remaining product-value feature (`AUT-15`) now that LLM parse normalization foundation exists.
- Technical debt and runtime warning cleanup can be delivered in parallel with clean boundaries.
- Keeps merge risk controlled by separating generation work from runtime warning work.

## Workstreams

### S7-A LLM Tailored Resume Generation

Linear issue: `AUT-15`
Branch: `codex/s7-a-llm-generation`
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s7_a_llm_generation`

Primary ownership:

- resume generation pipeline and LLM generation wiring
- generation-side contract and compliance gate integration
- generation-related tests

Out of scope:

- parser/runtime structural refactors
- sqlite/resource warning cleanup

### S7-B Parser/Runtime Technical Debt Cleanup

Linear issue: `AUT-16`
Branch: `codex/s7-b-runtime-cleanup`
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s7_b_runtime_cleanup`

Primary ownership:

- parser/runtime plumbing simplification
- readability/traceability refactors
- regression tests for touched areas

Out of scope:

- LLM resume generation feature expansion (`AUT-15`)
- sqlite lifecycle warning cleanup ownership (`AUT-23`)

### S7-C Test Runtime Resource Warning Cleanup

Linear issue: `AUT-23`
Branch: `codex/s7-c-runtime-warning-cleanup`
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s7_c_runtime_warning_cleanup`

Primary ownership:

- sqlite connection lifecycle cleanup in test/runtime flows
- warning-focused regression checks
- no behavior contract changes

Out of scope:

- broad parser/runtime refactor scope
- feature work

## Merge Order

1. `S7-C` runtime warning cleanup baseline
2. `S7-B` runtime/plumbing cleanup
3. `S7-A` LLM generation feature
4. integration verification pass

## Required Handoffs

- `sprints/sprint-07/handoffs/S7-A.md`
- `sprints/sprint-07/handoffs/S7-B.md`
- `sprints/sprint-07/handoffs/S7-C.md`

Each handoff must include:

- `STATUS: DONE` or `STATUS: BLOCKED`
- branch/worktree
- commit hash
- tests/checks run
- risks/assumptions
- explicit contract notes

## Reflection Requirement

Each thread must submit reflection:

- `sprints/sprint-07/thread-reflections/S7-A.md`
- `sprints/sprint-07/thread-reflections/S7-B.md`
- `sprints/sprint-07/thread-reflections/S7-C.md`

Integration reflection:

- `sprints/sprint-07/thread-reflections/S7-INTEGRATION.md`
