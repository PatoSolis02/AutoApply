STATUS: DONE

branch: codex/rc-a-simplify
worktree path: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_rc_a_simplify
final commit hash: 223e755

files changed summary:
- autoapply/service.py
  - Simplified claim-map construction by extracting section-specific claim building into `_build_section_claims` and iterating a section/source map.
- backend/app/runtime_generation.py
  - Reduced duplication by extracting DB not-found translation and typed mapping helpers for profile entries and render sections/bullets.
- backend/app/main.py
  - Centralized repeated JSON object validation and required non-empty string field extraction for API handlers.
- backend/tests/test_tracking_api.py
  - Added coverage that status/update and generate endpoints reject non-object JSON payloads with the expected 400 response.

tests run + results:
- `/bin/zsh -lc "PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'"`
  - PASSED: Ran 18 tests in 9.239s (OK)
- `PYTHONPATH=. python3 -m unittest discover tests`
  - PASSED: Ran 14 tests in 0.004s (OK)
- `npm test` (initial run)
  - FAILED: `vitest: command not found`
- `npm ci`
  - PASSED: installed dependencies (189 packages)
- `npm test` (after install)
  - PASSED: 3 files, 6 tests (all passed)

key simplifications made:
- Replaced repeated claim-map loops with a single section-driven helper flow in generation service.
- Replaced repeated profile/render conversion blocks with dedicated mapper helpers in sqlite generation repository.
- Replaced repeated request-payload checks in HTTP handlers with reusable validation helpers while keeping error payload contracts intact.

residual risks:
- Helper extraction is behavior-preserving by intent, but still touches hot serialization/parsing paths; regressions are mainly around malformed persisted JSON shapes not explicitly covered by tests.
- Frontend tests depend on local `node_modules`; clean worktrees require `npm ci` before `npm test`.
