## Scope Delivered
S6-A delivered AUT-13 contract mismatch hardening across backend API compatibility and frontend API client normalization. Work stayed inside contract/fallback behavior and regression coverage; no UI redesign or LLM feature expansion was introduced.

## What Changed
- Added backend endpoint compatibility so resume parse accepts both canonical `/api/v1/profile/resume-parse` and legacy `/api/v1/profile/ingest` in `backend/app/main.py`.
- Added backend multipart field compatibility to accept legacy `resume` upload field when canonical `file` is missing.
- Hardened frontend request path handling and fallback behavior in `src/lib/api.ts`:
  - supports endpoint variant retries for capture and resume upload paths on `404`
  - normalizes supported response envelope variants (`root`, `data`, `result`, nested objects)
  - emits explicit `502` errors for unsupported/missing contract keys instead of ambiguous failures.
- Added regression tests for endpoint/path drift and envelope drift:
  - `backend/tests/test_resume_upload_api.py`
  - `src/lib/api.test.ts`

## Validation
- `npm test -- src/lib/api.test.ts` passed (9 tests).
- `PYTHONPATH=backend python3 -m unittest backend/tests/test_resume_upload_api.py backend/tests/test_capture_api.py` passed (9 tests).

## Risks / Follow-ups
- Compatibility allowances (`/profile/ingest`, `resume` field, envelope wrappers) should be monitored and eventually retired once all clients consistently use canonical contract shapes.
- Capture fallback only includes one legacy path variant (`/capture`); if additional historical paths exist, they should be added explicitly with tests.
- Current contract mismatch surfaces are explicit, but integrating structured observability (AUT-14) will improve diagnosis speed further.

## Contract Notes
- Build contract invariants are preserved; canonical endpoints and payload contracts are unchanged.
- Changes are backward-compatible hardening only.
- Safety/compliance rules are unaffected (human-in-the-loop, truth-bound behavior, deterministic fallback expectations remain intact).
