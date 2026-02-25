# Sprint 08 Linear Issue Set

Project: `AutoApply`
Sprint label: `sprint-08`
Date initialized: 2026-02-25

## Selected Implementation Issues

1. `AUT-17` Advanced audit export for larger histories
- Status: `Done`
- Branch: `codex/s8-a-audit-export`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_a_audit_export`

2. `AUT-18` Fit scoring and gap analysis
- Status: `Done`
- Branch: `codex/s8-b-fit-scoring`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_b_fit_scoring`

3. `AUT-19` Packaging and release documentation hardening
- Status: `Done`
- Branch: `codex/s8-c-release-docs`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_c_release_docs`

Deferred:

- `AUT-20` remains `Backlog` for overflow/capacity.

## Sprint Tracking Issues

1. `AUT-26` Integrate Sprint 08 handoffs into codex/integration
- Status: `Done`
- Blocked by: `AUT-17`, `AUT-18`, `AUT-19`

2. `AUT-27` Sprint 08 recap and backlog rerank
- Status: `Todo`
- Blocked by: `AUT-26`

## Status Flow for This Sprint

1. `Backlog` -> `Todo` at sprint selection
2. `Todo` -> `In Progress` when branch/worktree is active
3. `In Progress` -> `In Review` on handoff completion
4. `In Review` -> `Done` after merge + verification on `codex/integration`

## Integration Outcome

Integrated on: 2026-02-25

Merge commits on `codex/integration`:

1. `3337dfa` (`S8-A`)
2. `3e6e7d7` (`S8-B`)
3. `5ec5347` (`S8-C`)

Verification:

- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'` -> PASS (`64 tests`)
- `PYTHONPATH=. python3 -m unittest discover tests` -> PASS (`25 tests`)
- `npm test` -> PASS (`8 files, 29 tests`)
- `npm run build` -> PASS

Next tracking issue:

- `AUT-27` remains `Todo` for sprint recap/backlog rerank.
