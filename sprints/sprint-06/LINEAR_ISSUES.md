# Sprint 06 Linear Issue Set

Project: `AutoApply`
Sprint label: `sprint-06`
Date initialized: 2026-02-24

## Selected Implementation Issues

1. `AUT-13` Contract mismatch and fallback hardening
- Status: `Done`
- Branch: `codex/s6-a-contract-fallback`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_a_contract_fallback`

2. `AUT-11` End-to-end workflow smoke tests in CI
- Status: `Done`
- Branch: `codex/s6-b-e2e-smoke`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_b_e2e_smoke`

3. `AUT-12` LLM-assisted resume parsing normalization
- Status: `Done`
- Branch: `codex/s6-c-llm-parse-normalization`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_c_llm_parse_normalization`

4. `AUT-14` Runtime and API observability improvements
- Status: `Done`
- Branch: `codex/s6-d-observability`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_d_observability`

## Sprint Tracking Issues

1. `AUT-21` Integrate Sprint 06 handoffs into codex/integration
- Status: `Done`
- Blocked by: `AUT-11`, `AUT-12`, `AUT-13`, `AUT-14`

2. `AUT-22` Sprint 06 recap and backlog rerank
- Status: `Todo`
- Blocked by: `AUT-21`

## Status Flow for This Sprint

1. `Backlog` -> `Todo` at sprint selection
2. `Todo` -> `In Progress` when branch/worktree is active
3. `In Progress` -> `In Review` on handoff completion
4. `In Review` -> `Done` after merge + verification on `codex/integration`

## Integration Outcome

Integrated on: 2026-02-24

Merge commits on `codex/integration`:

1. `3ea2581` (`S6-A`)
2. `68550ec` (`S6-C`)
3. `c490e11` (`S6-D`)
4. `b0e1951` (`S6-B`)

Verification:

- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'` -> PASS (`50 tests`)
- `PYTHONPATH=. python3 -m unittest discover tests` -> PASS (`22 tests`)
- `npm test` -> PASS (`8 files, 29 tests`)
- `npm run build` -> PASS
