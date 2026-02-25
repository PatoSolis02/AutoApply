# S9-B Reflection (AUT-32)

## Summary
Delivered capture reliability hardening for LinkedIn-first real pages by improving extractor fallback logic, making missing-field recovery guidance actionable, and adding deterministic fixture regressions for layout variants.

## What Worked
1. Treating job-id recovery as a first-class concern (`currentJobId`, active-card data attributes, JSON-LD identifiers) materially reduced job URL extraction fragility across list/detail layouts.
2. JSON-LD scoring with `currentJobId` preference resolved ambiguous multi-posting payloads deterministically.
3. Adding fixture-driven regression cases made extractor behavior easy to validate while iterating on selector/fallback heuristics.
4. Surfacing backend field-level validation details in Capture UI significantly improved recovery clarity versus generic 400 messaging.

## Friction
1. This worktree initially lacked npm dependencies, which blocked the first test run until `npm ci` was executed locally.
2. Canonical URL normalization changed previous test expectations that asserted tracking-query preservation; assertions had to be updated to stable view URLs.

## Residual Risks
1. LinkedIn may continue to ship DOM experiments that bypass current selectors; ongoing fixture expansion is still required for high reliability.
2. Shorter fallback description acceptance can capture less contextual text on sparse cards, which may reduce downstream matching quality in edge cases.

## Follow-Ups
1. Add fixture coverage for mobile/responsive LinkedIn job detail DOMs and A/B class-name variants.
2. Add lightweight telemetry around extractor missing-field categories to prioritize future selector/fallback investments.
3. Add a small browser-level smoke harness that validates extension extraction against archived real-page snapshots before release.

## Commit
- `876ef3a`
