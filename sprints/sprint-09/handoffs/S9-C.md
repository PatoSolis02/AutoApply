STATUS: DONE

branch: `codex/s9-c-generation-format-contract`
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_c_generation_format_contract`
issue: `AUT-37`
commit hash: `c3fd2c0`

scope delivered:
1. Added versioned generated-resume format contract (`resume_format.v1`) with explicit baseline anchor to `artifacts/resume_samples/Redacted Resume.pdf`.
2. Defined canonical section ordering and labels aligned to baseline-supported schema sections:
- `Education`
- `Work Experience`
- `Projects`
- `Skills`
3. Added runtime conformance validator for generated render models:
- new module `autoapply/generation_format_contract.py`
- contract checks enforced before artifact write in `autoapply/artifacts.py`
4. Updated deterministic generation output shape and persistence compatibility:
- include `education` section in render model JSON serialization/deserialization
- include education claim mapping in generation service
5. Updated generated artifact rendering to contract order/labels and added HTML metadata tags for contract version + baseline anchor.
6. Added architecture documentation for generation format contract and linked it from build contract.
7. Added regression tests for contract conformance and section-order behavior.

files changed:
- `autoapply/generation_format_contract.py`
- `autoapply/tailoring.py`
- `autoapply/service.py`
- `autoapply/artifacts.py`
- `autoapply/contracts.py`
- `backend/app/runtime_generation.py`
- `docs/architecture/GENERATION_FORMAT_CONTRACT.md`
- `docs/architecture/BUILD_CONTRACT.md`
- `tests/test_generation_format_contract.py`
- `tests/test_tailoring.py`
- `tests/test_generation_pipeline.py`

tests/checks run:
1. `PYTHONPATH=. python3 -m unittest tests.test_generation_format_contract tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api`
- PASS (`Ran 14 tests`)
2. `PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api`
- PASS (`Ran 11 tests`)
3. `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`
- PASS (`Ran 64 tests`)

assumptions/risks:
1. Baseline `Clubs` section is intentionally excluded from `resume_format.v1` because current MVP profile schema does not have clubs/activities fields.
2. Education bullets are currently synthesized from canonical education fields (school/degree/field/date) and may require wording/layout refinement in a future template iteration.
3. Contract validator currently treats unknown section keys as violations; adding new sections requires explicit contract version bump and validator updates.

contract notes:
1. Build-contract invariant is preserved: output format is now explicitly versioned and checked against a defined contract.
2. This thread does not change capture/auth behavior and does not change automatic profile-evidence selection runtime policy (`AUT-38` remains separate).
3. Contract metadata is now embedded in generated HTML for traceability:
- `autoapply-resume-format-contract=resume_format.v1`
- `autoapply-resume-format-baseline=artifacts/resume_samples/Redacted Resume.pdf`
