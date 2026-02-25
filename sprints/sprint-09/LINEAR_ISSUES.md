# Sprint 09 Linear Issue Set

Project: `AutoApply`
Sprint label: `sprint-09`
Date initialized: 2026-02-25

## Selected Implementation Issues

1. `AUT-34` Auth backend session and token contract
- Status: `Done`
- Branch: `codex/s9-a-auth-backend`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_a_auth_backend`

2. `AUT-32` Real-job capture reliability hardening for MVP
- Status: `Done`
- Branch: `codex/s9-b-capture-reliability`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_b_capture_reliability`

3. `AUT-37` Generation format contract using redacted resume baseline
- Status: `Done`
- Branch: `codex/s9-c-generation-format-contract`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_c_generation_format_contract`

## Sprint Tracking Issues

1. `AUT-40` Integrate Sprint 09 handoffs into codex/integration
- Status: `Done`
- Blocked by: `AUT-34`, `AUT-32`, `AUT-37`

2. `AUT-41` Sprint 09 recap and backlog rerank
- Status: `Todo`
- Blocked by: `AUT-40`

## Integration Outcome

- Merge order executed:
  - `codex/s9-a-auth-backend` -> `9895130`
  - `codex/s9-b-capture-reliability` -> `4b5be4e`
  - `codex/s9-c-generation-format-contract` -> `03b6f35`
- Verification on `codex/integration`:
  - `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'` -> PASS (`Ran 73 tests`)
  - `PYTHONPATH=. python3 -m unittest discover tests` -> PASS (`Ran 29 tests`)
  - `npm test` -> PASS (`8 files, 33 tests`)
  - `npm run build` -> PASS

## Status Flow for This Sprint

1. `Backlog` -> `Todo` at sprint selection
2. `Todo` -> `In Progress` when branch/worktree is active
3. `In Progress` -> `In Review` on handoff completion
4. `In Review` -> `Done` after merge + verification on `codex/integration`
