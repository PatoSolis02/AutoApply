STATUS: DONE

branch: `codex/s5-capture-reliability`

worktree path: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_b_capture_reliability`

commit hash: `e31c026`

scope delivered:
- Hardened LinkedIn extension extraction fallbacks across top-card, list-card, and metadata variants in `extension/content.js`.
- Reduced required-field extraction failures by adding deterministic fallbacks for title/company/description when right-panel selectors are missing.
- Added deterministic extractor fixtures/tests for new variants:
  - active list-card fallback
  - text-only top-card company/location
  - meta description fallback

tests/checks run + results:
- `npm test -- src/test/linkedinExtractor.test.ts` -> PASS (1 file, 5 tests)
- `npm test` -> PASS (8 files, 23 tests)

assumptions/risks:
- LinkedIn DOM churn remains an ongoing risk; selector/fallback fixture updates will still be needed as markup shifts.
- New list-card and meta fallbacks prioritize reliability (required-field completeness) over full-detail richness when right-panel content is unavailable.
- Location remains optional by contract and is now filtered heuristically to avoid obvious non-location metadata values.

contract notes:
- No backend or parser contract changes were made.
- Capture payload keys and required fields remain unchanged: `title`, `company`, `job_url`, `description_raw`, `captured_at` (with optional `location`).
