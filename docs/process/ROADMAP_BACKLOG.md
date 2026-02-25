# AutoApply Roadmap and Backlog

Last updated: 2026-02-25  
Owner: Integration/Product thread

## Source of Truth

MVP scope and gates are defined in:

- `docs/process/MVP_SCOPE.md`

If any backlog item conflicts with that file, `MVP_SCOPE.md` wins.

## Current Snapshot

- Sprint 08 implementation is integrated on `codex/integration`.
- Core local-first flow exists, but MVP focus is being reset to prevent feature drift.
- Current planning priority is to close MVP-critical gaps before additional non-essential features.

## Priority Model

Use both labels and rank order:

- `MVP-P0`: required for MVP acceptance criteria
- `MVP-P1`: reliability/usability required for practical MVP use
- `POST-MVP`: valuable, but not required for first release

Gate:

- Do not schedule `POST-MVP` work while `MVP-P0` items remain open, unless explicitly approved as a dependency unblocker.

## Ordered Active Task Queue (MVP-First)

1. `MVP-P0` Account auth baseline
- Scope: signup/login/logout/session persistence; per-user data boundary.
- Why now: user-facing MVP requires account and login as entry point.
- Linear: `AUT-28`.

2. `MVP-P0` Resume ingest -> profile auto-fill + editable sections
- Scope: parse resume and auto-populate profile sections (experiences/projects/skills), with user edits persisted.
- Why now: required input foundation for controlled tailoring.
- Builds on: `AUT-12` parsing normalization foundation.
- Linear: `AUT-29`.

3. `MVP-P0` Controlled tailored generation contract
- Scope: user chooses skills/projects/experiences/keywords for a specific job generation request.
- Also required: explicit generated resume format contract/template.
- Why now: directly maps to MVP value proposition.
- Builds on: `AUT-15` generation foundation.
- Linear: `AUT-30`.

4. `MVP-P0` Core tracking usability and correctness
- Scope: create/update/view core application statuses with practical user workflow coverage.
- Why now: required final stage of MVP manual-apply loop.
- Linear: `AUT-31`.

5. `MVP-P0` Capture reliability hardening
- Scope: raise capture success on real pages and strengthen error recovery guidance.
- Why now: pipeline entry quality directly controls MVP success.
- Linear: `AUT-32`.

6. `MVP-P1` End-to-end MVP acceptance tests
- Scope: deterministic tests covering login -> capture -> ingest -> controlled generate -> manual apply tracking.
- Builds on: `AUT-11` smoke baseline.
- Linear: `AUT-33`.

7. `MVP-P1` Resume parser quality hardening for common resume variants
- Scope: improve extraction reliability for core profile fields used in generation controls.

## Post-MVP Queue

These are not sprint-selection candidates while `MVP-P0` remains open:

1. `AUT-17` Advanced audit export for larger histories
2. `AUT-18` Fit scoring and gap analysis
3. `AUT-20` Non-critical refactor and polish cleanup

Operational/support lane (allowed only when it unblocks MVP execution):

1. `AUT-19` Packaging and release documentation hardening

## Recently Completed (Integrated)

Sprint 06:

- `AUT-11` End-to-end workflow smoke tests in CI
- `AUT-12` LLM-assisted resume parsing normalization
- `AUT-13` Contract mismatch and fallback hardening
- `AUT-14` Runtime/API observability improvements

Sprint 07:

- `AUT-15` LLM-based tailored resume generation
- `AUT-16` parser/runtime technical debt cleanup
- `AUT-23` test runtime resource warning cleanup

Sprint 08:

- `AUT-17` advanced audit export for larger histories
- `AUT-18` fit scoring and gap analysis
- `AUT-19` packaging and release documentation hardening

## Sprint Selection Rules

1. Select from `MVP-P0` first.
2. Add `MVP-P1` only if no `MVP-P0` is blocked by missing dependencies.
3. Keep thread scopes non-overlapping; one owner per task.
4. Reserve `POST-MVP` for explicitly approved exceptions.

## Working Backlog Rules

1. Every delivered thread handoff must include:
- commit hash
- tests run
- contract assumptions/risks

2. Sprint close requires:
- `sprints/<sprint>/SPRINT_LOG.md`
- `sprints/<sprint>/RETROSPECTIVE.md`
- per-thread reflections
- backlog refresh in this file

3. Every two sprints, run maintenance threads using:
- `docs/process/MAINTENANCE_THREADS.md`
