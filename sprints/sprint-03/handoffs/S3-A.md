STATUS: DONE

branch: `codex/s3-ci-guardrails`  
worktree path: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s3_a_ci_guardrails`  
commit hash: `326882d`

## Scope Delivered (S3-A Only)

1. Added CI pipeline in `.github/workflows/ci.yml` with fail-fast guardrails and test/build stages.
2. Added runtime version enforcement script:
   - `scripts/check_runtime_versions.py`
   - Enforces `python3 >= 3.11`, `node 24.x`, `npm 11.x`.
3. Added tracked generated/vendor artifact regression guard:
   - `scripts/check_tracked_artifacts.py`
   - Fails if blocked tracked paths/patterns appear (`node_modules`, `artifacts`, `backend/data`, `dist`, `coverage`, `.vite`, `*.tsbuildinfo`, `*.pyc`, `__pycache__`, generated `vite.config.js/.d.ts`).
4. Added local guardrail scripts in `package.json`:
   - `check:runtime`
   - `check:hygiene`
   - `check:guardrails`
5. Updated baseline tooling doc to include S3 guardrail commands:
   - `docs/process/TOOLING_BASELINE.md`

## Tests/Checks Run + Results

1. `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_runtime_versions.py` -> **FAIL**
   - local `python3` is `3.9.6` (below required `3.11.x`)
   - local `node` `24.13.1` and `npm` `11.8.0` pass
2. `python3 scripts/check_tracked_artifacts.py` -> **PASS**
3. `npm ci` -> **PASS**
4. `npm test` -> **PASS** (`3` files, `6` tests)
5. `npm run build` -> **PASS**
6. `PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api` -> **PASS** (`8` tests)
7. `PYTHONPATH=src python3 -m unittest tests.test_ws_d_audit_compliance` -> **PASS** (`6` tests)
8. `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'` -> **PASS** (`18` tests)

## Assumptions/Risks

1. CI uses `actions/setup-python@v5` with `python-version: 3.11`, so runtime enforcement should pass in CI even though local `python3` is `3.9.6`.
2. Artifact guard currently enforces a fixed blocked-pattern list; if new generated paths are introduced later, the script must be updated or drift can occur.

## What Worked

1. Guardrails are fail-fast and isolated in a dedicated CI gate job (`guardrails`).
2. Frontend test/build and Python suites run independently after guardrail pass, reducing debugging ambiguity.
3. Hygiene checks successfully prevent tracked generated/vendor regressions without impacting feature behavior.

## What Broke

1. Local `python3` runtime baseline mismatch (`3.9.6` vs required `>=3.11`) caused expected guardrail failure.

## Improve Next Sprint

1. Standardize local Python bootstrap (`3.11`) to align developer machines with CI baseline.
2. Add guardrail checks into a single documented preflight command for all threads before handoff.
3. Consider adding optional guardrail coverage for additional transient artifacts if new toolchains are introduced.

## Contract Deltas Requested

None.
