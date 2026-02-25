STATUS: DONE

issue: `AUT-18`
branch: `codex/s8-b-fit-scoring`
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_b_fit_scoring`
implementation commit hash: `780c1ef`

scope delivered:
1. Added deterministic fit scoring engine in `backend/app/fit_scoring.py` that computes weighted alignment (`requirements`, `keywords`, `preferred`) and stable gap items for missing evidence.
2. Enriched `GET /api/v1/applications` responses with computed `fit_score` values from profile/job structured data.
3. Enriched `GET /api/v1/applications/{id}` and `GET /api/v1/applications/{id}/audit-export` with `fit_analysis` payloads (coverage, matched/missing groups, actionable gaps, notes).
4. Added regression coverage for deterministic repeated-input scoring and profile-missing gap behavior.

out of scope preserved:
1. No `AUT-17` audit export scalability implementation.
2. No `AUT-19` release docs hardening work.

tests/checks run:
1. `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`
- PASS (`Ran 61 tests`)

assumptions/risks:
1. Fit analysis currently depends on existing structured job posting extraction quality from `build_structured_job_posting`; weak/missing requirement extraction can reduce scoring precision.
2. Matching is token-threshold based for determinism and traceability, so nuanced semantic equivalence is intentionally out of scope.
3. If profile data is missing, `fit_score` remains `null` and gap output highlights profile-evidence remediation instead of synthesizing a numeric score.

contract notes:
1. Approval/compliance invariants are unchanged: no generation-path bypasses, no status-transition rule changes, and no relaxation of `ready_to_apply` gate behavior.
2. Build/Safety contracts remain preserved (human-in-the-loop, truth-bound outputs, deterministic fallback expectations untouched).
3. API additions are additive response fields (`fit_analysis` plus computed `fit_score`) and do not remove or rename existing contract fields.
