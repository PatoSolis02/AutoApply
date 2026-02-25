# Sprint 09 Plan

Date: 2026-02-25
Mode: Parallel thread-batch (3 implementation threads)
Owner: Integration/Product (`codex/integration`)

## Sprint 09 Selection (MVP-P0 Child Stories)

Selected Linear issues:

1. `AUT-34` Auth backend session and token contract
2. `AUT-32` Real-job capture reliability hardening for MVP
3. `AUT-37` Generation format contract using redacted resume baseline

Tracking issues:

- `AUT-40` Integrate Sprint 09 handoffs into codex/integration
- `AUT-41` Sprint 09 recap and backlog rerank

## Why This Batch

- All selected items are small, independently shippable MVP-P0 stories.
- Boundaries are clean enough for parallel work with low file overlap risk.
- This batch improves MVP foundations without reintroducing broad-story drift.

## Workstreams

### S9-A Auth Backend Contract

Linear issue: `AUT-34`  
Branch: `codex/s9-a-auth-backend`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_a_auth_backend`

Primary ownership:

- backend signup/login/logout/session contract
- auth error semantics and session-expiry behavior
- backend contract tests

Out of scope:

- frontend auth UI route guards (`AUT-35`)
- per-user entity scoping migrations (`AUT-36`)

### S9-B Capture Reliability Hardening

Linear issue: `AUT-32`  
Branch: `codex/s9-b-capture-reliability`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_b_capture_reliability`

Primary ownership:

- LinkedIn-first capture extraction hardening
- required-field fallback behavior
- deterministic capture fixtures and regression tests

Out of scope:

- auth implementation (`AUT-34`)
- generation format/template contract work (`AUT-37`)

### S9-C Generation Format Contract

Linear issue: `AUT-37`  
Branch: `codex/s9-c-generation-format-contract`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_c_generation_format_contract`

Primary ownership:

- generation format contract definition
- baseline alignment to:
  - `artifacts/resume_samples/Redacted Resume.pdf`
- regression checks for contract conformance

Out of scope:

- automatic selection runtime behavior (`AUT-38`)
- capture/auth changes

## Merge Order

1. `S9-A` auth backend contract
2. `S9-B` capture reliability hardening
3. `S9-C` generation format contract
4. integration verification pass

## Required Handoffs

- `sprints/sprint-09/handoffs/S9-A.md`
- `sprints/sprint-09/handoffs/S9-B.md`
- `sprints/sprint-09/handoffs/S9-C.md`

Each handoff must include:

- `STATUS: DONE` or `STATUS: BLOCKED`
- branch/worktree
- commit hash
- tests/checks run
- risks/assumptions
- explicit contract notes

## Reflection Requirement

Each thread must submit reflection:

- `sprints/sprint-09/thread-reflections/S9-A.md`
- `sprints/sprint-09/thread-reflections/S9-B.md`
- `sprints/sprint-09/thread-reflections/S9-C.md`

Integration reflection:

- `sprints/sprint-09/thread-reflections/S9-INTEGRATION.md`
