STATUS: DONE

branch: `codex/s4-profile-ux`

worktree path: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s4_b_profile_ux`

commit hash: `76d3dc5`

tests/checks run + results:
- `npm test -- src/pages/ProfilePage.test.tsx src/lib/api.test.ts` -> PASS (2 files, 11 tests)
- `npm run build` -> PASS (`tsc -b` + Vite production build)

assumptions/risks:
- Assumed S4-A ingestion endpoint base is `POST /api/v1/profile/ingest` (overridable via `VITE_PROFILE_INGEST_PATH`) and upload field key is `resume`.
- UI upload parsing accepts S4-A response envelopes containing `profile`, `parsed_profile`, or direct profile payload with canonical profile keys.
- If S4-A returns a different endpoint/path, multipart field name, or payload key shape, upload mapping will fail with an explicit contract-mismatch error and requires alignment.
- No ingestion API contract changes were made in this branch; integration risk is strictly contract-shape mismatch until S4-A contract is finalized/merged.
