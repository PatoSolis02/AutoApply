# Tooling Baseline

This document defines the pinned runtime baseline and canonical test commands for the `codex/integration` trunk and Sprint 3 branches.

## Runtime Baseline

- Python: `3.11.x` minimum (`backend/pyproject.toml` enforces `requires-python = ">=3.11"`).
- Node.js: `24.x`.
- npm: `11.x`.

## Guardrail Commands

Run from repository root.

- `python3 scripts/check_runtime_versions.py`
- `python3 scripts/check_tracked_artifacts.py`

## Canonical Test Commands

Run from repository root unless noted.

### Frontend/UI

- `npm test`

### Python Domain/API (root tests)

- `PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api`
- `PYTHONPATH=src python3 -m unittest tests.test_ws_d_audit_compliance`

### Backend API package tests

- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`

## Notes

- If local `python3` is below `3.11`, install/select a `3.11.x` interpreter before running Python test commands.
- Guardrail checks are run first in CI before test/build jobs.
- Keep this file updated when runtime major/minor baselines or canonical test commands change.
