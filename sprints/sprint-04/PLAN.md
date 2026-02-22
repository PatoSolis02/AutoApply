# Sprint 04 Plan

Date: 2026-02-22  
Mode: Parallel (3 implementation threads)  
Owner: Architecture/Integration (`codex/integration`)

## Branching and Commit Policy

- Trunk branch: `codex/integration`.
- All workstreams develop on dedicated branches/worktrees, then merge back to trunk.
- Commit cadence:
  - Commit after each logical unit.
  - Keep commits reviewable and scoped.
  - Preserve behavior traceability in messages and tests.

## Sprint Goal

Complete the full Profile -> Tailored Resume workflow in UI:

1. Replace placeholder resume upload with real ingestion.
2. Make profile editing usable without raw JSON dependence.
3. Provide clear review/approval/audit visibility from capture through ready-to-apply.

## Workstreams

### S4-A Resume Ingestion Backend

Branch: `codex/s4-ingestion-backend`  
Primary scope:

- Resume upload parsing pipeline (`pdf`/`docx`) into canonical profile structures.
- Backend endpoint(s) for upload + parse output.
- Mapping quality and validation tests for parsed profile data.

### S4-B Profile Builder UX

Branch: `codex/s4-profile-ux`  
Primary scope:

- Structured profile editor (identity, summary, experiences, projects, skills, education).
- Upload flow wired to S4-A endpoint(s).
- Keep raw JSON editing as advanced fallback, not primary UX.

### S4-C End-to-End Workflow and Audit Visibility

Branch: `codex/s4-workflow-audit`  
Primary scope:

- UI flow: capture -> generate -> review -> approve -> ready_to_apply.
- Improved claims/change-log visibility in resume review surfaces.
- Basic audit export/view for traceability.
- End-to-end acceptance coverage of the intended user path.

## Merge Order

1. S4-A (backend ingestion contract first).
2. S4-B (profile UX wiring).
3. S4-C (end-to-end workflow + audit UX).
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

- `sprints/sprint-04/handoffs/S4-A.md`
- `sprints/sprint-04/handoffs/S4-B.md`
- `sprints/sprint-04/handoffs/S4-C.md`
