# S6-C Handoff - LLM Parsing Normalization (AUT-12)

STATUS: DONE

- branch: `codex/s6-c-llm-parse-normalization`
- worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s6_c_llm_parse_normalization`
- implementation commit: `01230d2`

## Scope Delivered

1. Implemented LLM-assisted normalization stage in `backend/app/resume_ingest.py` after deterministic parse extraction:
- normalization runs through `LlmRuntime.run_with_fallback(workflow="resume_parse")`
- deterministic parser output remains canonical fallback on disabled/misconfigured/provider/transform failures
- parse response now includes `normalization` metadata with mode/reason/provider/model/prompt version
2. Added traceability metadata for normalization outcomes:
- field-level change trace (`field`, `before`, `after`, optional source evidence line)
- `applied` + `change_count` for quick downstream diagnostics
3. Preserved deterministic behavior and fallback semantics:
- parse pipeline still validates the final profile contract (`resume_parse.v1`)
- invalid/non-JSON LLM output falls back deterministically (no hard failure path)
4. Added test coverage for LLM-enabled and LLM-disabled paths:
- parser unit tests for disabled fallback metadata, enabled success normalization, and invalid-LLM fallback
- runtime test ensuring transform errors trigger deterministic fallback
- API test updated to assert normalization envelope presence

## Explicit Out-of-Scope Preserved

- No full LLM-based resume generation feature work (`AUT-15`).
- No frontend flow changes beyond consuming existing `profile` + `warnings` behavior.

## Tests / Checks Run

1. `PYTHONPATH=. python3 -m unittest tests/test_llm_foundation.py`
- Result: `OK` (`Ran 8 tests`)
2. `PYTHONPATH=backend python3 -m unittest backend/tests/test_resume_ingest.py backend/tests/test_resume_upload_api.py`
- Result: `OK` (`Ran 19 tests`)
3. `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`
- Result: `OK` (`Ran 45 tests`)

## Assumptions / Risks

1. Provider clients remain unimplemented by default (foundation behavior), so real LLM normalization requires a provider implementation thread.
2. Normalization merge logic is contract-safe but conservative; it prioritizes deterministic structure preservation over aggressive re-structuring.
3. Trace evidence is line-substring based and may miss exact provenance for heavily rewritten normalized text.

## Prompt / Model Contract Notes

1. Workflow contract used: `resume_parse` with prompt version resolved from `AUTOAPPLY_LLM_PARSE_PROMPT_VERSION` (default `resume_parse.v1`).
2. Prompt message payload includes source resume lines, deterministic parse JSON, and deterministic warnings.
3. LLM response contract for normalization expects JSON object form with `{"profile": {...}}` (or direct profile object fallback parsing).
4. Parse response now surfaces runtime metadata: `mode`, `reason`, `provider`, `model`, `prompt_version`, `applied`, `change_count`, and `changes`.

## Files Changed

- `autoapply/llm/runtime.py`
- `backend/app/resume_ingest.py`
- `backend/tests/test_resume_ingest.py`
- `backend/tests/test_resume_upload_api.py`
- `tests/test_llm_foundation.py`
