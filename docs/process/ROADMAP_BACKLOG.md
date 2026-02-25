# AutoApply Roadmap and Backlog

Last updated: 2026-02-25
Owner: Integration/Product thread

## Current Snapshot

- Sprint 7 integrated on `codex/integration`.
- Core flow remains operational: capture -> generate -> review -> approve -> ready_to_apply.
- Reliability and generation gains now in place:
  - contract fallback hardening (`AUT-13`)
  - deterministic API workflow smoke tests in CI (`AUT-11`)
  - LLM-assisted parse normalization with deterministic fallback (`AUT-12`)
  - structured request observability with request IDs (`AUT-14`)
  - LLM-based tailored resume generation with deterministic fallback (`AUT-15`)
  - parser/runtime technical debt cleanup (`AUT-16`)
  - sqlite runtime warning cleanup (`AUT-23`)
- Remaining roadmap focus is advanced product features, packaging/release hardening, and low-risk cleanup.

## Priority Scale

- `1` = highest priority, blocks roadmap progress
- `2` = high priority, should follow immediately after priority 1
- `3` = important, can run after core stability work
- `4` = medium, value-add after core delivery
- `5` = low, polish or deferable work

## Linear Translation Rules

When creating/updating Linear issues from this backlog:

1. Use backlog IDs (`Q-*`, `B-*`, `F-*`, `C-*`) as references in description only.
2. Do not prefix Linear issue titles with backlog IDs.
3. Use labels for classification (`quality`, `Bug`, `Feature`, `cleanup`, and `fg-*` feature groups).
4. Use full story sections from `docs/process/LINEAR_WORKFLOW.md`:
- `Why`
- `Scope`
- `Out of scope`
- `Exit criteria`
- `Definition of done`

## Recently Completed (Integrated)

Sprint 05:

- `Q-1` Resume parsing field accuracy
- `B-1` PDF extraction edge-case fixes
- `F-1` LLM provider integration foundation
- `Q-2` LinkedIn capture reliability hardening
- `Q-3` Human-friendly UI/navigation improvements

Sprint 06:

- `Q-4` End-to-end workflow smoke tests in CI (`AUT-11`)
- `F-2` LLM-assisted resume parsing normalization (`AUT-12`)
- `B-2` Contract mismatch and fallback hardening (`AUT-13`)
- `C-1` Runtime/API observability and diagnosability (`AUT-14`)

Sprint 07:

- `F-3` LLM-based tailored resume generation (`AUT-15`)
- `C-2` Cleanup technical debt in parser/test/runtime plumbing (`AUT-16`)
- `C-5` Test runtime resource warning cleanup (`AUT-23`)

## Ordered Active Task Queue (Execution Order)

1. `F-4` Advanced audit export for larger histories (`AUT-17`) - Priority `4`
2. `F-5` Fit scoring phase execution (`AUT-18`) - Priority `4`
3. `C-3` Packaging and release documentation hardening (`AUT-19`) - Priority `4`
4. `C-4` Non-critical refactor/polish cleanup (`AUT-20`) - Priority `5`

## Feature Work

- `F-4` Advanced audit export - Priority `4`
- Scope: large-history handling (pagination/chunking/stream/file export path).
- Exit criteria: predictable export behavior for large histories without regressions.

- `F-5` Fit scoring - Priority `4`
- Scope: score jobs by alignment and provide gap analysis.
- Exit criteria: stable scoring contract and actionable gap output.

## Cleanup and Technical Debt

- `C-3` Release/packaging docs cleanup - Priority `4`
- Scope: operational docs for extension/app packaging and repeatable release steps.
- Exit criteria: reproducible release runbook validated against current workflow.

- `C-4` Low-impact refactors - Priority `5`
- Scope: naming consistency, minor reorganizations, non-behavioral cleanup.
- Exit criteria: readability improvements with no functional change.

## Parallelization Policy (No Overlap)

- Use as many threads as makes sense for independent ownership lanes.
- Maximize parallelism only when scope boundaries are clear and file overlap is minimal.
- One task should have one owner thread at a time.
- If two tasks touch the same primary files/contracts, keep them in one thread or sequence them.

Parallel assignment rules:

1. Assign by ownership boundary, not by equal team size.
2. Create a file/path ownership map before kickoff.
3. Do not run parallel threads with overlapping write scope unless integration owner explicitly approves.
4. Route cross-thread contract changes through integration owner first.
5. Merge in dependency order: foundations -> features -> UX wiring -> test hardening/docs.

Recommended active split for current queue:

1. Thread A: advanced audit export lane
- `F-4`

2. Thread B: fit scoring lane
- `F-5`

3. Thread C: operations/docs release lane
- `C-3`

4. Thread D: polish cleanup lane (optional, capacity permitting)
- `C-4`

## Sprint Structure Recommendation (Thread-Batch Model)

Sprint meaning in this repo:

- A sprint is the group of threads run in parallel together, then integrated, recapped, and reprioritized.
- It is a delivery batch model first; calendar length is secondary.

How to decide which threads/tasks run together:

1. Start from top of `Ordered Active Task Queue`.
2. Take highest-priority tasks that are dependency-ready.
3. Build a candidate batch using non-overlapping ownership boundaries:
- different primary files/directories
- no conflicting contract edits
- minimal merge collision risk
4. Stop adding tasks when overlap risk rises or integration complexity becomes high.
5. Launch each selected task as its own thread + worktree.

Recommended batch size:

- Usually 3-5 parallel threads.
- Expand only when ownership is cleanly separable.
- Reduce when task coupling is high.

Capacity guardrail:

- Keep 20-30% capacity for regressions/hotfixes discovered during integration.

## Working Backlog Rules

1. Every delivered thread must update its handoff with:
- commit hash
- tests run
- contract assumptions/risks

2. Sprint close requires:
- `sprints/<sprint>/SPRINT_LOG.md`
- `sprints/<sprint>/RETROSPECTIVE.md`
- per-thread reflections
- roadmap/backlog update in this file

3. Every two sprints, run maintenance threads using:
- `docs/process/MAINTENANCE_THREADS.md`

4. Private sample artifacts (resumes, sensitive docs) stay untracked under:
- `artifacts/`
