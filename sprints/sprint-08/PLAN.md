# Sprint 08 Plan

Date: 2026-02-25
Mode: Parallel thread-batch (3 implementation threads)
Owner: Integration/Product (`codex/integration`)

## Sprint 08 Selection (from Linear)

Selected Linear issues:

1. `AUT-17` Advanced audit export for larger histories
2. `AUT-18` Fit scoring and gap analysis
3. `AUT-19` Packaging and release documentation hardening

Deferred:

- `AUT-20` Non-critical refactor and polish cleanup (kept in backlog for overflow/capacity)

Tracking issues:

- `AUT-26` Integrate Sprint 08 handoffs into codex/integration
- `AUT-27` Sprint 08 recap and backlog rerank

## Why This Batch

- Sprint 07 completed the core LLM generation and runtime hygiene foundation.
- Sprint 08 now targets next product capabilities (`AUT-17`, `AUT-18`) and operational readiness (`AUT-19`).
- `AUT-20` is intentionally deferred to avoid overlap risk while feature lanes are active.

## Workstreams

### S8-A Advanced Audit Export

Linear issue: `AUT-17`  
Branch: `codex/s8-a-audit-export`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_a_audit_export`

Primary ownership:

- large-history audit export behavior
- export limits/failure handling and regression coverage

Out of scope:

- fit scoring implementation (`AUT-18`)
- release documentation hardening (`AUT-19`)

### S8-B Fit Scoring and Gap Analysis

Linear issue: `AUT-18`  
Branch: `codex/s8-b-fit-scoring`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_b_fit_scoring`

Primary ownership:

- scoring model and gap-analysis contract
- test coverage for stability and output semantics

Out of scope:

- audit export scalability implementation (`AUT-17`)
- release docs scope (`AUT-19`)

### S8-C Packaging and Release Docs

Linear issue: `AUT-19`  
Branch: `codex/s8-c-release-docs`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_c_release_docs`

Primary ownership:

- packaging/release runbooks and validation steps
- consistency and accuracy of operational documentation

Out of scope:

- new runtime product behavior
- feature implementation in `AUT-17` or `AUT-18`

## Merge Order

1. `S8-A` advanced audit export
2. `S8-B` fit scoring and gap analysis
3. `S8-C` release docs hardening
4. integration verification pass

## Required Handoffs

- `sprints/sprint-08/handoffs/S8-A.md`
- `sprints/sprint-08/handoffs/S8-B.md`
- `sprints/sprint-08/handoffs/S8-C.md`

Each handoff must include:

- `STATUS: DONE` or `STATUS: BLOCKED`
- branch/worktree
- commit hash
- tests/checks run
- risks/assumptions
- explicit contract notes

## Reflection Requirement

Each thread must submit reflection:

- `sprints/sprint-08/thread-reflections/S8-A.md`
- `sprints/sprint-08/thread-reflections/S8-B.md`
- `sprints/sprint-08/thread-reflections/S8-C.md`

Integration reflection:

- `sprints/sprint-08/thread-reflections/S8-INTEGRATION.md`

## Maintenance Boundary Reminder

Sprint 08 is a maintenance-boundary sprint (`every two sprints`).  
Run organizer/refactor maintenance threads after Sprint 08 integration and before Sprint 09 selection, using `docs/process/MAINTENANCE_THREADS.md`.
