# AutoApply Roadmap and Backlog

Last updated: 2026-02-25  
Owner: Integration/Product thread

## Source of Truth

MVP scope and gates are defined in:

- `docs/process/MVP_SCOPE.md`

If any backlog item conflicts with that file, `MVP_SCOPE.md` wins.

## Current Snapshot

- Sprint 09 implementation is integrated on `codex/integration`.
- Core local-first flow exists with stronger auth/capture/format contracts.
- Current planning priority is to close remaining MVP-P0 delivery gaps before any post-MVP scope.

## Priority Model

Use both labels and rank order:

- `MVP-P0`: required for MVP acceptance criteria
- `MVP-P1`: reliability/usability required for practical MVP use
- `POST-MVP`: valuable, but not required for first release

Gate:

- Do not schedule `POST-MVP` work while `MVP-P0` items remain open, unless explicitly approved as a dependency unblocker.

## Ordered Active Task Queue (MVP-First)

1. `MVP-P0` Complete account auth baseline
- Scope: finish auth UX and enforce per-user ownership boundaries across profile/applications.
- Why now: backend auth primitives are done; MVP still needs protected UX and data isolation.
- Linear: `AUT-28` (umbrella), `AUT-35`, `AUT-36`.

2. `MVP-P0` Resume ingest -> profile auto-fill + editable sections
- Scope: parse resume and auto-populate profile sections (experiences/projects/skills), with user edits persisted.
- Why now: required input foundation for controlled tailoring.
- Builds on: `AUT-12` parsing normalization foundation.
- Linear: `AUT-29`.

3. `MVP-P0` Complete controlled tailored generation runtime behavior
- Scope: LLM receives full saved profile data plus job data and automatically selects best-fit evidence.
- Why now: format contract is done; MVP still needs automatic evidence selection behavior.
- Builds on: `AUT-15` generation foundation and `AUT-37` format contract delivery.
- Linear: `AUT-30` (umbrella), `AUT-38`.

4. `MVP-P0` Core tracking usability and correctness
- Scope: create/update/view core application statuses with practical user workflow coverage.
- Why now: required final stage of MVP manual-apply loop.
- Linear: `AUT-31`.

5. `MVP-P1` End-to-end MVP acceptance tests
- Scope: deterministic tests covering login -> capture -> ingest -> controlled generate -> manual apply tracking.
- Builds on: `AUT-11` smoke baseline.
- Linear: `AUT-33`.

6. `MVP-P1` Resume parser quality hardening for common resume variants
- Scope: improve extraction reliability for core profile fields used in generation controls.
- Linear: `AUT-39` (fixture expansion/eval harness).

## Post-MVP Queue

These are not sprint-selection candidates while `MVP-P0` remains open:

1. `AUT-20` Non-critical refactor and polish cleanup

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

Sprint 09:

- `AUT-32` real-job capture reliability hardening for MVP
- `AUT-34` auth backend session and token contract
- `AUT-37` generation format contract using redacted resume baseline

## Sprint Selection Rules

1. Select from `MVP-P0` first.
2. Add `MVP-P1` only if no `MVP-P0` is blocked by missing dependencies.
3. Keep thread scopes non-overlapping; one owner per task.
4. Reserve `POST-MVP` for explicitly approved exceptions.

## Story Decomposition Policy

1. Keep umbrella stories for outcome tracking (for example `AUT-28`, `AUT-30`).
2. Execute delivery through smaller implementation stories with clear boundaries (for example `AUT-34` to `AUT-39`).
3. Prefer stories that can be completed in one thread without cross-owner overlap.

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
