# Sprint 06 Retrospective

Date closed: 2026-02-24  
Project: AutoApply (local-first MVP)  
Sprint type: Reliability + observability + LLM parsing quality

## Sprint Goal

Deliver the selected Sprint 06 Linear scope:

- `AUT-13` Contract mismatch and fallback hardening
- `AUT-11` End-to-end workflow smoke tests in CI
- `AUT-12` LLM-assisted resume parsing normalization
- `AUT-14` Runtime and API observability improvements

## Delivery Model

- Sprint selected from Linear backlog using `sprint-06` label and status workflow.
- Parallel execution in isolated worktrees and dedicated branches.
- Integration performed on `codex/integration` with planned merge ordering.

## What Was Delivered

Contract hardening (`AUT-13`):

- backend endpoint compatibility for resume parse legacy path and multipart field alias support
- frontend API fallback/response envelope normalization hardening
- explicit `502` mismatch surfaces for unsupported contract envelopes
- regression tests for fallback and envelope drift behavior

Workflow smoke checks (`AUT-11`):

- deterministic API-level smoke flow for capture -> generate -> review -> approve -> audit
- stage-tagged diagnostics in smoke assertions
- CI `workflow-smoke` job in `.github/workflows/ci.yml`

LLM parse normalization (`AUT-12`):

- LLM-assisted normalization stage in resume ingest path
- deterministic fallback retained when LLM is unavailable/invalid
- normalization metadata and field-level change trace included in response
- tests for enabled/disabled/fallback behaviors

Observability (`AUT-14`):

- structured request lifecycle logs in backend runtime
- `X-Request-Id` propagation and generation behavior
- additive failure classification for common error categories
- no breaking API contract changes

## Validation Summary

Integration verification passed:

1. backend test suite: `50` tests passed
2. root python tests: `22` tests passed
3. frontend tests: `29` tests passed
4. frontend build: pass

## What Went Well

1. Linear-first sprint selection and status workflow reduced ambiguity at kickoff.
2. Worktree isolation prevented branch collisions during parallel execution.
3. Merge order minimized risk: contract hardening first, smoke validation last.
4. Thread handoffs/reflections were complete and usable for integration decisions.
5. Added observability made backend behavior easier to diagnose during tests.

## What Went Wrong

1. Backend test output is now noisy due to structured logs and sqlite resource warnings.
2. Some sprint recap artifacts in earlier sprints were missing, requiring format fallback to Sprint 1/2 style.
3. API-level smoke coverage still leaves extension/browser integration gaps.

## Root Causes

1. Test runtime does not consistently close sqlite handles under all code paths.
2. Logging verbosity is not currently environment-tuned for test mode.
3. Browser/extension smoke coverage was intentionally out of scope to keep sprint overlap low.

## Key Learnings

1. Linear status discipline (`Backlog` -> `Todo` -> `In Progress` -> `In Review` -> `Done`) should remain mandatory.
2. Reliability work benefits from pairing contract hardening with observability in the same sprint batch.
3. LLM-assisted workflows need explicit deterministic fallback and traceability from day one.
4. Smoke tests should remain focused and deterministic, then incrementally expand into cross-surface coverage.

## Action Items

Process:

1. Keep the Sprint Kickoff Protocol in `docs/process/LINEAR_WORKFLOW.md` as the required path for every sprint.
2. Ensure each sprint ships `SPRINT_LOG.md` and `RETROSPECTIVE.md` at close before moving backlog priorities.
3. Continue collecting thread reflections plus integration reflection each sprint.

Technical:

1. Add follow-up backlog item to eliminate sqlite `ResourceWarning` test/runtime leaks.
2. Add environment-based log verbosity control for test mode.
3. Plan a future browser/extension-assisted smoke lane to complement API smoke tests.

## Every-Two-Sprints Maintenance Trigger

Sprint 06 is an every-two-sprints boundary. Run both maintenance threads next:

1. Project Organizer thread
2. Code Refactorer thread

Canonical prompts are in:

- `docs/process/MAINTENANCE_THREADS.md`

## Current Standing

Sprint 06 outcome: **completed and integrated**.

Current active backlog for next sprint selection is now centered on:

- `AUT-15` LLM-based tailored resume generation
- `AUT-16` technical debt cleanup in parser/runtime plumbing
- `AUT-17` advanced audit export
- `AUT-18` fit scoring and gap analysis
- `AUT-19` packaging/release docs hardening
- `AUT-20` non-critical refactor/polish cleanup
- `AUT-23` test runtime resource warning cleanup
