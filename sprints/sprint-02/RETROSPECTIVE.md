# Sprint 02 Retrospective

Date closed: 2026-02-22  
Project: AutoApply (local-first MVP)  
Sprint type: Runtime parity + stabilization

## Sprint Goal

Deliver the Sprint 02 objectives from `sprints/sprint-02/PLAN.md`:

- P0: API endpoint parity for tracking UI and live compliance runtime wiring.
- P1: package layout unification and repository hygiene.

## Delivery Model

- Trunk/integration owner operated on `codex/integration`.
- Parallel workstreams executed in isolated branches/worktrees:
  - S2-A: platform API parity.
  - S2-B: compliance runtime wiring.
  - S2-C: package layout unification.
  - S2-D: repo hygiene and tooling baseline.
- Merge order followed plan: S2-D -> S2-C -> S2-A -> S2-B.

## What Was Delivered

S2-D Repo hygiene:

- `.gitignore` baseline and cleanup of tracked generated/vendor artifacts.
- runtime/tooling baseline documentation.
- commits: `99aa8f7`, `23b4ec1`, `8265077`.

S2-C Package layout:

- canonical Python package root unified under `autoapply/`.
- removed `src/autoapply` ambiguity and updated imports/tests.
- commits: `2ffb092`, `afb0aae`.

S2-A Platform API parity:

- live backend routes for list/detail/status/resume timeline/resume detail/approve.
- persistence and integration test coverage for API path behavior.
- commits: `9307bc1`, `31cf20c`, `830209c`.

S2-B Compliance runtime:

- compliance and approval gating wired into active runtime path.
- live API tests for `422/409/404` semantics and approval behavior.
- commits: `abee327`, `cecbabf`.

Integration and stabilization:

- merge commits: `23f21b3`, `d3a0ef4`, `91b240f`, `edf2d08`.
- post-merge correctness fix: `eb0b1b9` (status idempotency + ignore runtime artifacts).
- capture reliability hardening on LinkedIn variants:
  - `59edc74`, `aa7aabc`, `da9f2e5`, `ea1ff45`, `bb4cef8`.
- frontend runtime/parsing fix:
  - `b6f8beb` (Vite `/api` proxy + non-JSON API guardrail).
- profile data surface for generation inputs:
  - `ad15f8d` (`GET/PUT /api/v1/profile` + `/profile` UI + upload placeholder).

## Validation Summary

Integration validation checkpoints recorded during Sprint 02:

- backend API suite passed after integration: 14/14.
- python domain suites passed after unification: 14/14.
- frontend tests passed: 6/6.
- final sprint close verification after profile addition:
  - backend tests: 17/17 (`PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`)
  - frontend tests: 6/6 (`npm test`)
  - frontend build: pass (`npm run build`)

## What Went Well

1. Planned merge ordering reduced conflict blast radius.
2. Worktree isolation model held after Sprint 1 corrections.
3. Contract semantics were validated through live API tests, not only unit logic.
4. Integration branch stayed coherent with frequent commits and targeted fixes.
5. User-facing demo quality improved materially through capture and UI runtime hardening.

## What Went Wrong

1. Handoff file discipline was uneven in real time; not all artifacts arrived in folder before integration.
2. Extension capture remained brittle across LinkedIn DOM variants and needed several follow-up fixes.
3. Frontend dev runtime had proxy/config gaps that surfaced only during manual demo.
4. Sandbox constraints (socket binding/index lock/build outputs) required escalated execution for normal workflows.
5. Additional scope (profile API/UI placeholders) entered near sprint close, which improved product readiness but increased end-of-sprint churn.

## Root Causes

- Late manual demo surfaced browser/runtime variants that synthetic tests did not cover.
- Contract-level success criteria did not originally include extension DOM variant coverage and frontend proxy verification.
- Tooling/sandbox assumptions were not fully codified as "always escalate for X" guardrails.
- Reflection/handoff gates were defined but not enforced as a strict pre-merge checklist.

## Key Learnings

1. Include demo-path checks in acceptance criteria, not only API and unit tests.
2. Treat extension selector stability as a first-class quality axis with fixture-driven tests.
3. Keep one integration owner but require hard handoff gates before merge.
4. Capture and UI layers need explicit operational diagnostics to accelerate support.
5. Profile data entry should exist early because generation/compliance quality depends on it.

## Action Items for Sprint 03

Process:

1. Enforce mandatory handoff files for all threads before integration starts.
2. Add a sprint-end demo checklist covering extension capture, frontend route loading, and backend API health.
3. Keep a branch provenance table in `SPRINT_LOG.md` as commits land.

Technical:

1. Add extension extractor fixture tests for multiple LinkedIn page layouts.
2. Add backend endpoint contract tests for `/api/v1/profile` edge cases and validation details.
3. Implement real resume-file parsing pipeline behind the `/profile` upload placeholder.
4. Add frontend tests for profile page load/save error states and JSON validation UX.
5. Add a lightweight health endpoint and UI diagnostics panel for quicker local triage.

## Current Standing

Sprint 02 outcome: **completed and integrated**.

The project now has:

- live contract-aligned tracking APIs,
- compliance runtime wiring in active paths,
- repo/package baseline stabilization,
- hardened capture flow for multiple LinkedIn variants,
- working profile source-data interface with resume upload placeholder.
