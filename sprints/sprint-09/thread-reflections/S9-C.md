# S9-C Reflection (`AUT-37`)

## Summary
Defined and enforced a versioned generation format contract (`resume_format.v1`) anchored to the redacted baseline sample, with test coverage for section ordering and generated-output conformance.

## What Worked
1. Isolating format rules in `autoapply/generation_format_contract.py` gave one authoritative place for section order, labels, and validation logic.
2. Enforcing conformance at artifact write-time prevented silent output drift from deterministic/LLM generation paths.
3. Adding regression assertions for heading order and contract metadata made format regressions immediately detectable in CI.

## Friction
1. `artifacts/` is git-ignored, so baseline anchoring had to be represented as contract metadata/documentation rather than a tracked fixture in this branch.
2. Existing render model only carried experience/project bullets, so adding baseline-aligned `Education` required additive model/serialization updates across service and runtime repository parsing.

## Residual Risks
1. Baseline includes `Clubs`, which is not represented in current profile schema; future schema extension should bump contract version before adding that section.
2. Output layout remains deterministic/minimal and may still need visual polish to better match spacing/typography of baseline document style.

## Follow-Ups
1. If profile schema is extended with clubs/activities, introduce `resume_format.v2` with explicit section additions and migrations.
2. Add golden-file visual snapshot checks for generated HTML/PDF if/when tracked baseline fixtures become available in CI-safe form.

## Contract Notes
1. New explicit format contract doc: `docs/architecture/GENERATION_FORMAT_CONTRACT.md`.
2. Build contract now links to generation format contract and keeps baseline anchor invariant explicit.
3. Contract conformance is now runtime-enforced and test-covered for generated outputs.

## Commit
- `c3fd2c0`
