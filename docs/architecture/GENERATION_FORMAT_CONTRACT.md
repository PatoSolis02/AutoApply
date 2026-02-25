# Resume Generation Format Contract (v1)

Last updated: 2026-02-25  
Owner: Sprint 09 Thread C (`AUT-37`)

## Purpose

Define a versioned and testable output-format contract for generated resumes so generated HTML/PDF ordering stays stable across deterministic and LLM-assisted generation.

## Contract Version

- Format contract version: `resume_format.v1`
- Baseline artifact anchor: `artifacts/resume_samples/Redacted Resume.pdf`

## Baseline Alignment Notes

The redacted baseline sample is a single-page, sectioned resume with strong section hierarchy and top-to-bottom reading order.

Observed baseline section sequence:

1. `Education`
2. `Work Experience`
3. `Projects`
4. `Clubs`

`resume_format.v1` mirrors the baseline style for sections represented in the current MVP profile schema and generation model.

## Supported Sections (`resume_format.v1`)

Canonical generated output order:

1. `Education`
2. `Work Experience`
3. `Projects`
4. `Skills`

Section semantics:

- `Education` maps to `profile.education`.
- `Work Experience` maps to selected `profile.experiences`.
- `Projects` maps to selected `profile.projects`.
- `Skills` maps to selected skill keywords.

Notes:

- `Clubs` is intentionally excluded in `v1` because no clubs/activities field exists in the current profile contract.
- Sections with no content may be omitted, but present sections must preserve canonical ordering.

## Render Model Contract Requirements

For `RenderModel`:

1. Allowed `sections` keys: `education`, `experience`, `projects`.
2. Present section order must follow `education -> experience -> projects`.
3. Each section entry must have:
- non-empty `entry_id`
- at least one bullet
- bullets with non-empty `id` and `text`
4. `selected_skill_keywords` entries must be non-empty strings.

## Artifact Contract Requirements

Generated HTML/PDF output must:

1. Preserve section order defined above.
2. Use heading labels:
- `Education`
- `Work Experience`
- `Projects`
- `Skills`
3. Include HTML metadata:
- `autoapply-resume-format-contract=resume_format.v1`
- `autoapply-resume-format-baseline=artifacts/resume_samples/Redacted Resume.pdf`

## Conformance Checks

Conformance is enforced in code by:

- `autoapply/generation_format_contract.py` validator (`assert_render_model_conforms`)
- `autoapply/artifacts.py` pre-write contract validation
- generation regression tests:
  - `tests/test_generation_format_contract.py`
  - `tests/test_generation_pipeline.py`
  - `tests/test_tailoring.py`

## Versioning Rules

When changing output format:

1. Bump contract version (`resume_format.vN`).
2. Update this document with new section ordering/rules.
3. Update validator and tests in the same change.
4. Keep previous version behavior documented for integration traceability.
