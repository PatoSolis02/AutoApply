STATUS: DONE

branch: `codex/s6-b-e2e-smoke`  
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_b_e2e_smoke`  
commit hash: `844610b`

## Scope Delivered (`AUT-11`)

- Added deterministic workflow smoke scenarios in `backend/tests/test_workflow_smoke_api.py`:
  - `test_smoke_primary_flow_capture_generate_review_approve_audit`
  - `test_smoke_ready_to_apply_is_blocked_before_approve`
- Added stage-specific failure labeling for diagnostics via assertion messages like `[stage=capture]`, `[stage=generate]`, `[stage=review]`, `[stage=approve]`, and `[stage=audit]`.
- Wired smoke checks into CI by adding `workflow-smoke` job in `.github/workflows/ci.yml`.
- Removed duplicate full-flow acceptance coverage from `backend/tests/test_tracking_api.py` so smoke ownership is explicit and centralized.
- Updated `docs/process/TOOLING_BASELINE.md` with the canonical smoke command.

## Tests / Checks Run

1. `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_workflow_smoke_api.py' -v`  
   - `Ran 2 tests`  
   - `OK`
2. `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`  
   - `Ran 43 tests`  
   - `OK`

## Contract Notes

- No API contract or build-contract behavior changes.
- Smoke tests validate existing contract flow only: capture -> generate -> review -> approve -> audit.

## Assumptions / Risks

- CI and normal local execution environments allow localhost server bind for backend API tests; in this sandbox, escalated execution was required for reliable bind behavior.
- Smoke coverage is API-level deterministic flow validation, not full browser/extension automation.
