# Sprint 06 Plan

Date: 2026-02-24
Mode: Parallel thread-batch (4 implementation threads)
Owner: Integration/Product (`codex/integration`)

## Sprint 06 Selection (from Linear Backlog)

Selected Linear issues:

1. `AUT-13` Contract mismatch and fallback hardening
2. `AUT-11` End-to-end workflow smoke tests in CI
3. `AUT-12` LLM-assisted resume parsing normalization
4. `AUT-14` Runtime and API observability improvements

Deferred (not in Sprint 06 batch):

- `AUT-15`, `AUT-16`, `AUT-17`, `AUT-18`, `AUT-19`, `AUT-20`

## Why This Batch

- Top-priority backlog items with clear delivery value.
- Low overlap ownership boundaries for parallel execution.
- Preserves contract stability while improving reliability and diagnosability.
- Keeps LLM parsing quality work moving without coupling to generation scope.

## Workstreams

### S6-A Contract Hardening

Linear issue: `AUT-13`
Branch: `codex/s6-a-contract-fallback`
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_a_contract_fallback`

Primary ownership:

- backend API contract/fallback handling
- related backend tests

Out of scope:

- UI redesign
- LLM generation feature expansion

### S6-B Workflow Smoke Tests

Linear issue: `AUT-11`
Branch: `codex/s6-b-e2e-smoke`
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_b_e2e_smoke`

Primary ownership:

- CI workflow definitions
- smoke/integration test scaffolding and fixtures

Out of scope:

- contract behavior changes
- parser algorithm refactors

### S6-C LLM Parsing Normalization

Linear issue: `AUT-12`
Branch: `codex/s6-c-llm-parse-normalization`
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_c_llm_parse_normalization`

Primary ownership:

- LLM-assisted parsing normalization path
- parser quality regression tests

Out of scope:

- full resume generation flow changes (`AUT-15`)

### S6-D Observability Improvements

Linear issue: `AUT-14`
Branch: `codex/s6-d-observability`
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_d_observability`

Primary ownership:

- structured logging/correlation IDs
- diagnosability improvements

Out of scope:

- external monitoring platform rollout
- unrelated refactors

## Merge Order

1. `S6-A` (contract hardening baseline)
2. `S6-C` (LLM parsing normalization)
3. `S6-D` (observability)
4. `S6-B` (smoke tests against integrated state)
5. integration verification pass

## Required Handoffs

- `sprints/sprint-06/handoffs/S6-A.md`
- `sprints/sprint-06/handoffs/S6-B.md`
- `sprints/sprint-06/handoffs/S6-C.md`
- `sprints/sprint-06/handoffs/S6-D.md`

Each handoff must include:

- `STATUS: DONE` or `STATUS: BLOCKED`
- branch/worktree
- commit hash
- tests/checks run
- risks/assumptions
- contract notes

## Reflection Requirement

Each thread must submit reflection:

- `sprints/sprint-06/thread-reflections/S6-A.md`
- `sprints/sprint-06/thread-reflections/S6-B.md`
- `sprints/sprint-06/thread-reflections/S6-C.md`
- `sprints/sprint-06/thread-reflections/S6-D.md`

Integration thread reflection:

- `sprints/sprint-06/thread-reflections/S6-INTEGRATION.md`

## Maintenance Reminder

Sprint 06 is an every-two-sprints boundary. At sprint close (after integration), run both maintenance threads from:

- `docs/process/MAINTENANCE_THREADS.md`
