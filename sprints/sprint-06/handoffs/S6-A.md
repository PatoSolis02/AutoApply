STATUS: DONE

branch: `codex/s6-a-contract-fallback`

worktree path: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_a_contract_fallback`

commit hash: `f16c212`

scope delivered:
- Hardened backend resume parse endpoint compatibility in `backend/app/main.py` by accepting both `/api/v1/profile/resume-parse` and legacy `/api/v1/profile/ingest`.
- Added backend multipart compatibility for legacy upload field alias (`resume`) when canonical `file` field is absent.
- Hardened frontend API contract handling in `src/lib/api.ts` for:
  - endpoint fallbacks (`capture`, `resume-parse`)
  - supported response envelope variants (`data`, `result`, nested resource objects)
  - explicit `502` mismatch errors when required contract IDs/profile payload are missing.
- Added regression coverage for known drift patterns in:
  - `backend/tests/test_resume_upload_api.py`
  - `src/lib/api.test.ts`

tests/checks run + results:
- `npm test -- src/lib/api.test.ts` -> PASS (1 file, 9 tests)
- `PYTHONPATH=backend python3 -m unittest backend/tests/test_resume_upload_api.py backend/tests/test_capture_api.py` -> PASS (9 tests)

assumptions/risks:
- Capture fallback currently supports canonical `/jobs/capture` and legacy `/capture`; unsupported custom paths still fail fast with explicit error surfaces.
- Envelope normalization intentionally tolerates common wrappers (`data`/`result`) but still requires canonical IDs/profile shape to avoid silently accepting malformed contracts.
- Backend legacy compatibility keeps old clients working but should be treated as transition support, not a replacement for canonical contract paths.

contract notes:
- Canonical contract paths and response shapes remain unchanged; this thread adds backward-compatible handling only.
- No compliance gate behavior was altered.
- Contract mismatch behavior is now explicit and diagnosable (`502` with mismatch-specific messages) for unsupported envelopes.
