# Sprint 01 Retrospective

Date closed: 2026-02-21  
Project: AutoApply (local-first MVP)  
Sprint type: Foundation + parallel pilot

## Sprint Goal

Build a functional MVP foundation across:

- LinkedIn job capture and local ingest.
- Application tracking UI.
- Resume tailoring/PDF generation pipeline.
- Truth and compliance enforcement.

## Delivery Strategy

- Single architecture-owner thread defined contracts and integration path.
- Parallel workstreams executed implementation:
  - WS-A: capture + ingest
  - WS-B: dashboard + tracking UI
  - WS-C: tailoring + generation pipeline
  - WS-D: audit + compliance
- Final integration happened on `codex/integration`.

## What Was Delivered

Docs/process artifacts:

- `docs/architecture/BUILD_CONTRACT.md`
- `docs/process/PARALLEL_WORKSTREAMS.md`
- `docs/process/THREAD_KICKOFFS.md`

WS-A delivery:

- Chrome extension extraction and capture trigger.
- `POST /api/v1/jobs/capture` implemented.
- SQLite capture schema/migration and insert path.
- Capture payload validation and ingest structuring.
- Capture API tests.

WS-B delivery:

- React pages for applications list/detail and resume version detail.
- Status transition editor UI and resume timeline UI.
- API client layer with `409` and `422` error messaging.
- Frontend tests and config corrections.

WS-C delivery:

- Tailoring engine and deterministic render model generation.
- Resume generation service with deterministic version IDs.
- Artifact writer pathing for HTML/PDF outputs.
- Generation endpoint adapter and tests.

WS-D delivery:

- Audit/compliance engine module.
- Claims map and change log behavior.
- Approval gate and status transition enforcement checks.
- WS-D compliance test suite.

## Integration Summary

Integrated branch: `codex/integration`  
Commit chain integrated:

1. `229cf7e` baseline (contains broad WS-A/WS-D plus project scaffolding)
2. `c52bfdf` WS-B configuration fix
3. `55b379f` WS-C finalize commit

Integrated verification run:

- `npm test -- --run` -> 6/6 passed
- `PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api` -> 8/8 passed
- `PYTHONPATH=src python3 -m unittest tests.test_ws_d_audit_compliance` -> 6/6 passed
- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'` -> 2/2 passed

## Thread Reflection Addendum

Additional findings from WS-A/WS-B/WS-C/WS-D closeout notes:

1. WS-A flagged extractor fragility risk:
   - LinkedIn selector changes can break capture.
   - Extension currently has no offline queue/retry behavior for backend outages.
2. WS-B confirmed UI scope is functionally built and tested, but runtime is blocked by missing backend route parity.
3. WS-C confirmed focused suite passes, while full discovery exposed cross-package integration friction (`autoapply.audit_compliance` import path mismatch).
4. WS-D confirmed policy behavior is strong at domain-test level, but API/runtime wiring is still required to guarantee identical `422/409/404` semantics in production paths.
5. Multiple threads observed environment/tooling variance (Python runtime feature compatibility, sandbox limits, dependency/tool availability) as recurring delivery friction.
6. WS-D branch provenance degraded during integration cleanup (branch pointer not preserved), reducing perfect traceability back to original thread branch head.

## What Went Well

1. Contract-first planning reduced architecture drift during parallel work.
2. Compliance and truth constraints were implemented in Sprint 1 instead of postponed.
3. Parallel execution produced meaningful output in all core domains (capture/UI/generation/compliance).
4. Integration branch reached a clean, testable state.

## What Went Wrong

1. Parallel Git setup started before a stable baseline commit, causing worktree setup failures.
2. Worktree/branch ownership was inconsistent early, causing branch collisions and restart overhead.
3. Planned handoff files were not consistently produced; integration required manual verification.
4. Python code now exists in multiple package roots (`autoapply/` and `src/autoapply/`), creating import ambiguity.
5. WS-B UI expects backend routes not yet fully implemented in the active backend server.
6. Baseline includes generated/vendor artifacts (`node_modules`, `__pycache__`, build artifacts), which increases repo noise.
7. Runtime/tooling baseline was not pinned early (for example Python feature drift such as `datetime.UTC` compatibility).
8. Test execution flow depended on environment-specific constraints (`pytest` availability, sandboxed socket/temporary directory behavior).
9. Capture robustness is incomplete (DOM selector brittleness and missing client-side retry queue).
10. Branch provenance for all thread artifacts was not consistently preserved through merge/integration steps.

## Root Cause Notes

- Process root cause: pre-flight checklist for parallelization was missing and not enforced before thread kickoff.
- Technical root cause: runtime boundaries were not finalized enough (single package root, single backend entrypoint).
- Operational root cause: handoff protocol was defined but not strictly required by all threads.
- Platform root cause: language/tool/runtime versions and test runner expectations were not standardized before parallel execution.

## Key Learnings

1. Parallel threads should not start until baseline commit and worktrees are verified.
2. Every thread must be constrained to one worktree and branch at kickoff.
3. Handoff artifacts must be mandatory, not optional.
4. Integration must validate both tests and runtime wiring against contract endpoints.
5. Repository hygiene must be part of sprint acceptance criteria.
6. Sprint kickoff must lock runtime/tooling baselines (Python version, test commands, dependency expectations).
7. Thread closeout must preserve provenance metadata (branch head + commit mapping) even if branches are later cleaned up.
8. For browser automation/capture modules, fixture-based selector regression testing is required from Sprint 1 onward.

## Action Items for Sprint 02

Process actions:

1. Add and enforce a pre-flight checklist:
   - baseline commit exists
   - worktrees created
   - thread branch verified
   - kickoff prompt issued
2. Require per-thread handoff files in sprint folder before integration begins.
3. Add daily contract drift review point in architecture-owner thread.
4. Require thread reflections as a sprint close gate and roll them into the top-level retrospective.
5. Record branch provenance ledger (`thread -> branch -> final commit`) before any branch cleanup.

Technical actions:

1. Unify Python package layout to one canonical root.
2. Implement missing backend routes expected by WS-B UI:
   - `GET /api/v1/applications`
   - `GET /api/v1/applications/{id}`
   - `PATCH /api/v1/applications/{id}/status`
   - `GET /api/v1/applications/{id}/resume-versions`
   - `GET /api/v1/resume-versions/{id}`
   - `POST /api/v1/resume-versions/{id}/approve`
3. Wire WS-D compliance logic into the live API/runtime path.
4. Add `.gitignore` and remove tracked generated artifacts from version control.
5. Standardize one backend test command matrix documented in repo.
6. Pin runtime baselines (Python and Node toolchain versions) and enforce in project setup docs.
7. Add capture extractor fixture tests for multiple LinkedIn DOM variants.
8. Add extension-side retry/queue behavior for transient localhost backend failures.
9. Keep API route handlers testable as pure functions with thin framework adapters to reduce dependency coupling.

## Parallelization Model for Next Sprint

Recommended split:

1. Architecture/Integration owner (single thread)
2. Platform/API thread
3. UI thread
4. Tailoring/Scoring thread
5. Compliance/Quality thread

Required thread completion payload:

- `STATUS: DONE|BLOCKED`
- branch name
- commit hash
- tests run and result
- assumptions/risks
- proposed contract deltas (if any)

## Current Standing

Sprint 1 outcome: **completed with integration caveats**.

You have a substantial implemented base across all core domains, with Sprint 2 now focused on runtime unification, backend endpoint parity, and repo hygiene to convert this from module-complete to fully wired product behavior.
