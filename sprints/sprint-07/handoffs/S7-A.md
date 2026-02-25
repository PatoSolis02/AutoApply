STATUS: DONE

branch: `codex/s7-a-llm-generation`
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s7_a_llm_generation`
commit hash: `e61d339`
issue: `AUT-15`

scope delivered:
1. Added LLM-assisted resume generation in `autoapply/service.py` on top of deterministic tailoring.
2. Enforced deterministic fallback for disabled/unconfigured/provider-error/transform-error paths via `LlmRuntime.run_with_fallback(workflow="resume_generate")`.
3. Restricted LLM influence to source-backed bullet rewording only, preserving bullet IDs and source mappings.
4. Preserved compliance and approval behavior:
- generation still passes through compliance gate before persistence
- unsupported claims/invalid profile still return `422`
- generated versions remain unapproved until explicit approval
5. Improved claim traceability for rewritten bullets by preserving baseline evidence text in `claims_map` while allowing `bullet_text` rewording.
6. Added contract coverage for generation success/fallback while preserving existing failure-path coverage.

files changed:
- `autoapply/service.py`
- `tests/test_generation_pipeline.py`

tests/checks run:
1. `PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api`
- PASS (`Ran 10 tests`)
2. `PYTHONPATH=backend python3 -m unittest backend.tests.test_compliance_runtime_api backend.tests.test_workflow_smoke_api backend.tests.test_tracking_api`
- PASS (`Ran 18 tests`)

assumptions/risks:
1. Provider clients are still foundation stubs by default; LLM-success behavior depends on configured provider implementation in runtime environment.
2. Prompt payload truncation (`12000` chars per serialized input segment) is a safety bound and may reduce context fidelity on very large postings/profiles.
3. Current LLM generation contract intentionally allows only rewording; no new bullet insertion/removal is accepted to keep claims mapping deterministic.

contract notes:
1. Build contract invariants remain intact (human approval gate, truth-bound claims, persistence, no bypass around compliance).
2. Safety/compliance rules remain enforced for every generation path, including LLM-assisted output.
3. API generation response envelope is unchanged (`resume_version_id`, `warnings`, `blocked_reasons`), so frontend integration behavior remains compatible.
