# S7-B Reflection (AUT-16)

## What Worked

1. Consolidating duplicated merge loops into one shared scaffold reduced structural complexity without forcing contract changes.
2. Adding regression tests for invalid updates and append behavior made refactor safety explicit on parser normalization paths.
3. Running both parser-level and API-level tests caught behavior regressions at multiple boundaries.

## What Was Tricky

1. Merge semantics are intentionally conservative (index-based and field-type guarded), so refactoring had to preserve several subtle `_NO_UPDATE` and required-field behaviors.
2. Parser module size makes local changes easy to over-scope; keeping edits limited to normalization/runtime plumbing reduced risk.

## Residual Risks

1. Resume ingest remains a large module; although merge plumbing is cleaner, additional decomposition work could still improve long-term maintainability.
2. Runtime provider behavior in production still depends on provider-client implementation quality outside this cleanup thread.

## Follow-Ups

1. Consider a future cleanup thread to separate normalization merge utilities from file extraction/parsing concerns in `backend/app/resume_ingest.py`.
2. Add integration-level fixtures for more diverse malformed LLM normalization payloads once generation-side AUT-15 work stabilizes.
