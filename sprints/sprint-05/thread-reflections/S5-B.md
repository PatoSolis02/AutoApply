## Scope Delivered
S5-B delivered Q-2 capture reliability hardening by strengthening the LinkedIn extractor in `extension/content.js` and expanding deterministic fixture coverage in `src/test/linkedinExtractor.test.ts`. Changes stayed within capture extension logic and capture-related tests only.

## What Changed
- Added resilient fallback extraction paths for title/company/location/description when primary right-panel selectors are absent.
- Added active list-card fallback logic so capture can still succeed when a selected job card is visible but detail markup is incomplete.
- Added text-only top-card parsing and metadata-based description fallback to reduce required-field misses (`company` and `description_raw`).
- Tightened location extraction to avoid obvious non-location metadata (applicant counts, recency chips, promo tags).

## Validation
- `npm test -- src/test/linkedinExtractor.test.ts` passed with all 5 extractor fixture tests.
- `npm test` passed with all 23 frontend tests.

## Risks / Follow-ups
- LinkedIn markup remains volatile, so fixture drift is still expected over time.
- Reliability fallback paths may capture shorter summary text when full right-panel description is unavailable; this is an intentional tradeoff to reduce hard capture failures.
- Additional real-world fixture harvesting from manual QA will improve confidence beyond synthetic variants.

## Contract Notes
No parser internals, backend APIs, or capture payload schema were changed. Build contract invariants remain intact, including user-initiated capture and existing `/api/v1/jobs/capture` request shape.
