# Sprint 03 Plan

Date: 2026-02-22  
Mode: Parallel (3 implementation threads)  
Owner: Architecture/Integration (`codex/integration`)

## Branching and Commit Policy

- Trunk branch: `codex/integration`.
- All workstreams develop on dedicated branches/worktrees, then merge back to trunk.
- Commit cadence:
  - Commit after each logical unit.
  - Avoid end-of-thread mega commits.
  - Keep commit messages scope-specific.

## Sprint Goal

Reliability + guardrails:

1. Lock critical behavior with automated checks.
2. Remove known capture/runtime brittleness.
3. Make contract-sensitive behavior explicitly test-enforced.

## Workstreams

### S3-A CI and Guardrails

Branch: `codex/s3-ci-guardrails`  
Primary scope:

- CI pipeline for backend + frontend test/build.
- Runtime version enforcement checks.
- Repository hygiene checks to block tracked generated/vendor artifacts.
- Fail-fast checks for artifact regression.

### S3-B Backend Contract Reliability

Branch: `codex/s3-backend-reliability`  
Primary scope:

- Approval/status coupling tests and idempotency tests.
- `/api/v1/profile` edge-case contract tests.
- Add `GET /health` endpoint for runtime health checks.
- Ensure contract error semantics remain explicit (`400/404/409/422`).

### S3-C Capture and Frontend Reliability

Branch: `codex/s3-capture-frontend-reliability`  
Primary scope:

- LinkedIn extractor fixture tests for multiple DOM/layout variants.
- Frontend tests for `/profile` load/save/error and JSON validation UX.
- Lightweight UI diagnostics panel consuming backend health/status signals.

## Merge Order

1. S3-A (guardrails first).
2. S3-B (backend contract lock).
3. S3-C (capture/frontend reliability and diagnostics).
4. Integration verification pass.

## Required Thread Handoff Format

Each thread must submit:

- `STATUS: DONE` or `STATUS: BLOCKED`
- branch name
- worktree path
- final commit hash
- tests run + summarized output
- assumptions/risks
- any contract deltas requested

Handoff files:

- `sprints/sprint-03/handoffs/S3-A.md`
- `sprints/sprint-03/handoffs/S3-B.md`
- `sprints/sprint-03/handoffs/S3-C.md`
