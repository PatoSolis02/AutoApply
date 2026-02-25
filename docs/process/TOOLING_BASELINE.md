# Tooling Baseline

Last updated: 2026-02-25

This document defines the pinned runtime baseline and canonical verification commands for `codex/integration` and active implementation branches/worktrees.

## Runtime Baseline

- Python: `3.11.x` minimum (`backend/pyproject.toml` enforces `requires-python = ">=3.11"`).
- Node.js: `24.x`.
- npm: `11.x`.

## Guardrail Commands

Run from repository root.

- `python3 scripts/check_runtime_versions.py`
- `python3 scripts/check_tracked_artifacts.py`

## Canonical Verification Commands (CI Parity)

Run from repository root unless noted.

### Frontend/UI

- `npm test`

### Python Domain/API (root tests)

- `PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api`
- `PYTHONPATH=src python3 -m unittest tests.test_ws_d_audit_compliance`

### Backend API package tests

- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`

### Workflow smoke tests

- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_workflow_smoke_api.py'`

## Release Gate Usage

- Treat this file as the command baseline for validation gates.
- Run these checks before artifact packaging/release using:
  - `docs/release/RELEASE_RUNBOOK.md`

## Notes

- If local `python3` is below `3.11`, install/select a `3.11.x` interpreter before running Python test commands.
- Guardrail checks are run first in CI before test/build jobs.
- Keep `PYTHONPATH=src` for `tests.test_ws_d_audit_compliance` unless CI is updated in `.github/workflows/ci.yml`.
- Keep this file updated when runtime major/minor baselines or canonical test commands change.
