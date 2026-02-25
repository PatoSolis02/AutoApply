# Process Docs Index

Last updated: 2026-02-25
Owner: Integration/Product thread

## Purpose

This index is the canonical entrypoint for process and planning docs.
Use it first, then open the specific process doc for the task at hand.

## Active Process Docs

1. `docs/process/MVP_SCOPE.md`
- Canonical MVP definition and in-scope/out-of-scope gates for sprint selection.

2. `docs/process/ROADMAP_BACKLOG.md`
- Priority queue, active task ordering, and sprint-batch selection source.

3. `docs/process/LINEAR_WORKFLOW.md`
- Linear object model, status protocol, dependency rules, and close checklist.

4. `docs/process/PARALLEL_WORKSTREAMS.md`
- Parallel thread/worktree guardrails and integration sequencing rules.

5. `docs/process/MAINTENANCE_THREADS.md`
- Every-two-sprints organizer/refactor maintenance lane kickoff templates.

6. `docs/process/TOOLING_BASELINE.md`
- Runtime baseline plus canonical verification commands.

## Companion Operational Docs

1. `docs/release/RELEASE_RUNBOOK.md`
- Canonical packaging/release runbook for backend, frontend, and extension artifacts.
- This replaces ad-hoc release command examples from historical sprint handoffs/reflections.

## Sprint Artifact Layout (Canonical)

For each active sprint directory `sprints/sprint-XX/`:

1. Top-level:
- `PLAN.md`
- `LINEAR_ISSUES.md` (optional but recommended when Linear is source of truth)
- `SPRINT_LOG.md`
- `RETROSPECTIVE.md`

2. `thread-kickoffs/`:
- `REQUEST_MESSAGES.md` (current sprint kickoff prompts)

3. `handoffs/`:
- `<thread-id>.md` (for example: `S6-A.md`, `MAINT-ORGANIZER.md`)

4. `thread-reflections/`:
- `<thread-id>.md`
- `<sprint-id>-INTEGRATION.md` when integration reflection is needed

## Legacy / Archived Process Docs

- `docs/process/THREAD_KICKOFFS.md` now points to current sprint-specific kickoff artifacts.
- The original generic WS-A/WS-B/WS-C/WS-D template is archived at:
  - `docs/process/archive/THREAD_KICKOFFS_LEGACY_WS.md`
