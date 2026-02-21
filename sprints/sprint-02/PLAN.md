# Sprint 02 Plan

Date: 2026-02-21  
Mode: Parallel (Mode A)  
Owner: Architecture/Integration

## Branching and Commit Policy

- Trunk branch for this sprint: `codex/integration`.
- All workstreams develop on their assigned Sprint 2 branches, then integrate back to `codex/integration`.
- Commit cadence:
  - Commit after each meaningful logical unit (not one giant end-of-thread commit).
  - Minimum expectation: setup commit + core implementation commit + tests/fixes commit.
  - Commit messages must clearly describe scope and impact.

## Objectives

P0:

1. Implement backend endpoint parity for WS-B UI routes.
2. Wire WS-D compliance/approval logic into live API runtime paths.

P1:

1. Unify Python package layout to one canonical package root.
2. Apply repository hygiene (`.gitignore`, remove generated/vendor artifacts from tracking).

## Workstreams

### S2-A Platform/API

Scope:

- Implement routes:
  - `GET /api/v1/applications`
  - `GET /api/v1/applications/{id}`
  - `PATCH /api/v1/applications/{id}/status`
  - `GET /api/v1/applications/{id}/resume-versions`
  - `GET /api/v1/resume-versions/{id}`
  - `POST /api/v1/resume-versions/{id}/approve`
- Ensure contract-compliant status and payloads.

Branch: `codex/s2-platform-api`

### S2-B Compliance Runtime Wiring

Scope:

- Integrate compliance enforcement into active backend runtime path.
- Ensure `422/409/404` semantics align with contract.
- Ensure no bypass path around approval/compliance gates.

Branch: `codex/s2-compliance-runtime`

### S2-C Package Layout Unification

Scope:

- Collapse Python package duplication to one canonical root.
- Update imports/tests/entrypoints to remove `autoapply` vs `src/autoapply` ambiguity.

Branch: `codex/s2-package-layout`

### S2-D Repo Hygiene and Tooling Baseline

Scope:

- Add/update `.gitignore`.
- Stop tracking generated/vendor artifacts.
- Document pinned runtime/tooling expectations (Python/Node/test commands).

Branch: `codex/s2-repo-hygiene`

## Merge Order

1. S2-D (hygiene baseline first).
2. S2-C (package layout normalization).
3. S2-A (endpoint parity).
4. S2-B (compliance runtime wiring and endpoint semantics finalization).
5. Integration verification pass.

## Required Thread Handoff Format

Each thread must produce:

- `STATUS: DONE` or `STATUS: BLOCKED`
- branch name
- final commit hash
- tests run + output summary
- risks/assumptions
- requested contract deltas (if any)

Handoff files:

- `sprints/sprint-02/handoffs/S2-A.md`
- `sprints/sprint-02/handoffs/S2-B.md`
- `sprints/sprint-02/handoffs/S2-C.md`
- `sprints/sprint-02/handoffs/S2-D.md`
