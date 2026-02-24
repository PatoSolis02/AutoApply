# AutoApply Roadmap and Backlog

Last updated: 2026-02-24
Owner: Integration/Product thread

## Current Snapshot

- Sprint 4 integrated on `codex/integration`.
- Core flow works: capture -> generate -> review -> approve -> ready_to_apply.
- Profile UX and resume upload exist end-to-end.
- PDF parsing reliability improved via hotfix (`10cf071`) with compressed stream + ToUnicode support.
- Remaining quality gap: some real resumes still parse imperfectly (content quality, not total failure).

## Priority Scale

- `1` = highest priority, blocks roadmap progress
- `2` = high priority, should follow immediately after priority 1
- `3` = important, but can run after core stability is in place
- `4` = medium, value-add after core delivery
- `5` = low, polish or deferable work

## Ordered Task Queue (Execution Order)

1. `Q-1` Resume parsing field accuracy (personal info, jobs/experience, skills) - Priority `1`
2. `B-1` Fix remaining PDF extraction edge cases (fonts/encodings/layout variants) - Priority `1`
3. `F-1` LLM provider integration foundation for parsing + generation workflows - Priority `1`
4. `Q-2` LinkedIn capture reliability hardening - Priority `2`
5. `Q-3` Human-friendly UI/navigation improvements for main flow - Priority `2`
6. `Q-4` End-to-end workflow smoke tests in CI - Priority `2`
7. `F-2` LLM-assisted resume parsing normalization and quality fallback - Priority `2`
8. `F-3` LLM-based tailored resume generation using job content + profile - Priority `2`
9. `C-1` Runtime/API observability and diagnosability - Priority `3`
10. `C-2` Cleanup technical debt in parser/test/runtime plumbing - Priority `3`
11. `F-4` Advanced audit export for larger histories - Priority `4`
12. `F-5` Fit scoring phase execution (`docs/architecture/PHASE_PLAN.md`) - Priority `4`
13. `C-3` Packaging and release documentation hardening - Priority `4`
14. `C-4` Non-critical refactor/polish cleanup - Priority `5`

## Quality Improvements

- `Q-1` Resume parsing field accuracy - Priority `1`
- Goal: correctly identify personal information, job history, and skills with minimal manual edits.
- Exit criteria: measurable extraction accuracy improvement on fixture corpus + lower correction rate in profile form.

- `Q-2` LinkedIn capture reliability - Priority `2`
- Goal: reduce extraction failures across list/detail/right-panel variants.
- Exit criteria: fewer "required fields missing" capture failures in manual QA.

- `Q-3` Human-friendly UI and navigation - Priority `2`
- Goal: improve usability and reduce friction in Profile -> Capture -> Review -> Approve.
- Exit criteria: clearer nav labels, lower click count, clearer validation and recovery messages.

- `Q-4` End-to-end workflow tests - Priority `2`
- Goal: prevent workflow regressions across backend + frontend + extension interaction points.
- Exit criteria: stable E2E smoke tests for capture -> generate -> review -> approve -> audit export.

## Bug Fixes

- `B-1` PDF extraction edge-case fixes - Priority `1`
- Scope: residual failures after hotfix (`10cf071`) on complex PDFs.
- Exit criteria: no hard extraction failure on tracked sample corpus; documented known unsupported patterns.

- `B-2` Contract mismatch and fallback hardening - Priority `2`
- Scope: ensure robust behavior if endpoint paths/response envelope variants drift.
- Exit criteria: stable backward-compatible handling and explicit error surfaces.

## Feature Work

- `F-1` LLM integration baseline - Priority `1`
- Scope: provider config, API client abstraction, model/prompt version contract, deterministic fallback behavior.
- Exit criteria: LLM can be enabled/disabled safely without breaking current deterministic flow.

- `F-2` LLM-assisted resume parsing quality - Priority `2`
- Scope: use LLM to normalize/repair extracted fields (skills, experience, personal details).
- Exit criteria: improved structured parse quality while preserving traceability.

- `F-3` LLM-driven resume tailoring generation - Priority `2`
- Scope: generate resumes from job content + user profile with safety/compliance gates intact.
- Exit criteria: reliable generation quality with claims mapping still enforced.

- `F-4` Advanced audit export - Priority `4`
- Scope: large-history handling (pagination/chunking/stream/file export path).

- `F-5` Fit scoring - Priority `4`
- Scope: score jobs by alignment and provide gap analysis.

## Cleanup and Technical Debt

- `C-1` Observability improvements - Priority `3`
- Scope: structured logs, correlation IDs, clearer diagnostics.

- `C-2` Codebase cleanup and simplification - Priority `3`
- Scope: remove brittle parser code paths, reduce complexity, improve traceability.

- `C-3` Release/packaging docs cleanup - Priority `4`
- Scope: operational docs for extension/app packaging and repeatable release steps.

- `C-4` Low-impact refactors - Priority `5`
- Scope: naming consistency, minor reorganizations, non-behavioral cleanup.

## Parallelization Policy (No Overlap)

- Use as many threads as makes sense for independent ownership lanes.
- Maximize parallelism only when scope boundaries are clear and file overlap is minimal.
- One task should have one owner thread at a time.
- If two tasks touch the same primary files/contracts, keep them in the same thread or sequence them.

Parallel assignment rules:

1. Assign by ownership boundary, not by equal team size.
2. Create a file/path ownership map before kickoff.
3. Do not run parallel threads with overlapping write scope unless integration owner explicitly approves.
4. Route all cross-thread contract changes through integration owner first.
5. Merge in dependency order: foundations -> features -> UX wiring -> test hardening/docs.

Recommended active split for current queue (example, topic-safe):

1. Thread A: deterministic parsing + PDF edge-case fixes
- `Q-1`, `B-1`

2. Thread B: capture reliability
- `Q-2`, `B-2` (capture contract/fallback hardening)

3. Thread C: UX/navigation and flow ergonomics
- `Q-3`

4. Thread D: LLM platform + generation features
- `F-1`, `F-2`, `F-3`

5. Thread E: QA, observability, and technical debt cleanup
- `Q-4`, `C-1`, `C-2`

## Sprint Structure Recommendation

Use a consistent 2-week sprint with topic-based goals.

1. Planning and partitioning (Day 1)
- Pick highest-priority items from the ordered queue.
- Partition into non-overlapping threads using file ownership map.
- Define contract assumptions and integration order up front.

2. Parallel build window (Days 2-7)
- Threads execute independently with minimal cross-talk.
- Mid-sprint checkpoint only for blockers or contract deltas.
- Keep one owner per task and per primary file area.

3. Integration and hardening (Days 8-9)
- Integration owner merges by dependency order.
- Resolve conflicts, run full backend/frontend test suites, run smoke flow.
- Handle only P0/P1 regressions before sprint close.

4. Demo and close (Day 10)
- Demo highest-priority user-visible improvements.
- Publish sprint log, retrospective, and thread reflections.
- Update this backlog with new priorities, carry-overs, and risks.

Capacity and guardrails:

- Reserve 20-30% sprint capacity for bug fixes/regressions/hotfixes.
- Limit each thread to one primary objective plus one secondary objective.
- A sprint is complete only when integration branch is stable and documented.

Integration thread responsibilities:
- Merge and resolve cross-thread contract conflicts.
- Keep contracts/types stable on `codex/integration`.
- Maintain this file and sprint-level recap artifacts.

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

3. Private sample artifacts (resumes, sensitive docs) stay untracked under:
- `artifacts/`
