STATUS: DONE

branch: codex/s3-capture-frontend-reliability
worktree path: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s3_c_capture_frontend_reliability
commit hash: 5ed973a

tests/checks run + results:
- `npm test -- src/test/linkedinExtractor.test.ts` -> PASS (3/3)
- `npm test -- src/pages/ProfilePage.test.tsx` -> PASS (7/7)
- `npm test -- src/pages/ProfilePage.test.tsx src/test/linkedinExtractor.test.ts` -> PASS (10/10)
- `npm test` -> PASS (16/16)

assumptions/risks:
- Chose existing `/api/v1/applications` + `/api/v1/profile` signals for diagnostics to avoid contract drift.
- Status-card counts represent current paginated payload, not an all-record aggregate.
- Extractor fixtures cover major observed variants but LinkedIn UI changes remain a standing reliability risk.

what worked:
- Commit-per-unit cadence kept scope controlled (extractor tests, profile tests, diagnostics panel).
- Fixture strategy produced deterministic extraction checks for fallback behavior.
- Mocked `/profile` UI tests now lock key UX contracts: load, save, error handling, and JSON validation.

what broke:
- JSDOM differences (`innerText`, URL/history origin) initially caused extractor timeouts.
- Missing cleanup in early UI tests created false failures from duplicated rendered trees.

what to improve next sprint:
- Centralize extension content-script test harness helpers in shared test utilities.
- Add a backend-provided aggregate status summary endpoint if diagnostics should show exact global lifecycle distribution.
- Establish a standard test-router wrapper with future flags enabled to reduce warning noise and future upgrade friction.
