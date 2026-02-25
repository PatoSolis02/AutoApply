STATUS: DONE

issue: `AUT-32`
branch: `codex/s9-b-capture-reliability`
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_b_capture_reliability`
implementation commit hash: `876ef3a`

scope delivered:
1. Hardened LinkedIn-first capture extraction in `extension/content.js` with stronger job-id/job URL recovery, top-card metadata parsing, JSON-LD multi-posting selection by `currentJobId`, and fallback title support from metadata.
2. Strengthened required-field fallback behavior by reducing false negatives in description extraction thresholds and expanding location/company/title fallback sources for real-page layout variance.
3. Improved user-facing recovery guidance for capture failures:
- extractor missing-field responses are now field-specific and actionable,
- extension popup maps API field validation errors to concrete recovery hints,
- manual Capture page now surfaces backend `errors[]` details with field-specific remediation.
4. Added deterministic regression fixtures/tests for known DOM/layout variants:
- JSON-LD multi-posting pages with current-job matching,
- active-list layouts with `data-occludable-job-id` and inline top-card metadata,
- deterministic missing-fields guidance response assertions.

out of scope preserved:
1. No auth/session implementation changes (`AUT-34` / `AUT-28` umbrella).
2. No resume generation format/template contract changes (`AUT-37` / `AUT-30` umbrella).

tests/checks run:
1. `npm test -- src/test/linkedinExtractor.test.ts src/pages/CapturePage.test.tsx`
- PASS (`Test Files 2 passed`, `Tests 11 passed`)

assumptions/risks:
1. LinkedIn DOM is inherently unstable; selector coverage is expanded but still dependent on LinkedIn not fully removing top-card/list semantics.
2. Canonical job URL normalization now prefers stable `https://www.linkedin.com/jobs/view/<id>` links; downstream consumers relying on tracking query params should not assume query preservation.
3. Lowered description fallback thresholds improve capture success but may admit shorter/less-rich text on sparse job cards; downstream ranking/parsing quality still depends on available source text.

contract notes:
1. `BUILD_CONTRACT` invariants are preserved: capture remains user-initiated, local-first, and human-in-the-loop with no autonomous submission behavior.
2. `/api/v1/jobs/capture` request/response contract is unchanged; this thread only improves extraction input quality and UI/extension guidance paths.
3. `MVP_SCOPE` capture reliability goals are directly addressed (LinkedIn-first robustness, required-field recovery guidance, deterministic regression fixtures) without expanding into out-of-scope auth/generation work.
