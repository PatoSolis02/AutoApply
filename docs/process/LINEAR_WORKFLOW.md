# Linear Workflow Guide

Last updated: 2026-02-25
Owner: Integration/Product thread

## Purpose

This doc defines how AutoApply uses Linear for sprint-batch planning, execution tracking, integration, and retrospectives.

## Core Principle

Use Linear as the execution control plane; use git/worktrees as the implementation plane.

- Linear tracks: priority, ownership, status, blockers, dependencies, recap.
- Git tracks: branches, commits, tests, integrations.

MVP gate source:

- `docs/process/MVP_SCOPE.md`

## Object Model

1. Project
- Single project: `AutoApply`

2. Cycle
- One cycle per sprint-batch (for example: `Sprint 05`)
- Sprint here means a selected group of non-overlapping parallel threads

3. Issues
- One issue per active thread workstream
- One integration issue per sprint-batch
- One retrospective issue per sprint-batch

4. Feature groups (epic-like)
- Use labels as feature-group/epic buckets for backlog organization.
- Keep one primary feature-group label on each backlog issue.

## Story Naming Standard

Use outcome-focused titles without type prefixes.

- Use: `End-to-end workflow smoke tests in CI`
- Avoid: `Q-4 End-to-end workflow smoke tests in CI`

Rules:

1. Do not prefix issue titles with `Q-`, `B-`, `F-`, `C-`, or sprint IDs.
2. Keep backlog reference IDs in the description (`Backlog reference: <id>`).
3. Keep labels responsible for classification (`quality`, `Bug`, `Feature`, `cleanup`).

## Story Definition Standard

Every backlog issue must include these sections in description:

1. `Backlog reference` and `Priority`
2. `Why`
3. `Scope`
4. `Out of scope`
5. `Exit criteria`
6. `Definition of done`

This is the minimum quality bar for thread kickoff readiness.

## Required Fields Per Thread Issue

Put these in description if custom fields are unavailable:

- Backlog IDs (for example: `Q-1`, `B-1`)
- Priority (mapped from `docs/process/ROADMAP_BACKLOG.md`)
- Branch name
- Worktree path
- Scope and out-of-scope
- Handoff file path
- Definition of done

## Priority Mapping

- Repo `1` -> Linear `Urgent`
- Repo `2` -> Linear `High`
- Repo `3` -> Linear `Medium`
- Repo `4` -> Linear `Low`
- Repo `5` -> Linear `No priority`

## Labels

Standard label set:

- topic labels: `quality`, `bug`, `feature`, `cleanup`
- technical labels: `llm`, `capture`, `ux`, `parser`, `integration`
- cycle label: `sprint-XX`
- MVP priority labels:
  - `mvp-p0`
  - `mvp-p1`
  - `post-mvp`
- feature-group labels:
  - `fg-core-reliability`
  - `fg-llm-intelligence`
  - `fg-user-experience`
  - `fg-platform-ops`
  - `fg-advanced-product`

MVP gating rule:

1. Every backlog issue must carry exactly one of `mvp-p0`, `mvp-p1`, or `post-mvp`.
2. Do not select `post-mvp` sprint work while open `mvp-p0` issues remain, unless explicitly approved as dependency unblockers.

## Dependency Rules

1. Every sprint-batch includes an integration issue.
2. Integration issue is blocked by all thread issues.
3. Retrospective issue is blocked by integration issue.
4. Do not start dependent work if blocker issues are unresolved.

## Status Rules

Use these statuses consistently:

1. `Todo`
- issue defined, not started

2. `In Progress`
- thread actively coding in its assigned worktree

3. `In Review`
- handoff complete, waiting for integration

4. `Done`
- merged into `codex/integration` and verified

5. `Blocked`
- cannot continue without external dependency/decision

## Sprint Kickoff Protocol (Linear-First)

At sprint start, select work only from Linear `Backlog` issues and move selected items through kickoff states.

Required kickoff sequence:

1. Validate candidate issues against `docs/process/MVP_SCOPE.md` and confirm MVP label (`mvp-p0`, `mvp-p1`, or `post-mvp`).
2. Select sprint batch from Linear backlog by MVP gate + dependency readiness.
3. Apply sprint label (`sprint-XX`) to selected issues.
4. Move selected implementation issues to `Todo`.
5. Move each issue to `In Progress` only when:
- dedicated branch/worktree is created
- owner thread has started coding
6. Move issue to `In Review` when handoff is complete and awaiting integration.
7. Move issue to `Done` only after merge + verification on `codex/integration`.

Sprint tracking issues:

1. Create one integration issue in `Todo`, blocked by all selected implementation issues.
2. Create one retrospective issue in `Todo`, blocked by integration issue.

## Worktree Enforcement

Every `In Progress` thread must have a unique worktree.

Required checks before moving issue to `In Progress`:

1. Branch exists from `codex/integration`
2. Worktree exists and is unique
3. `git worktree list` shows no collisions

## Integration Protocol

When thread issues move to `In Review`:

1. Integration issue owner merges by declared merge order.
2. Run verification suite on `codex/integration`.
3. Post integration result comment with commit hashes + test outcomes.
4. Move integrated thread issues to `Done`.

## Required Completion Comment Template

Use this on every thread issue:

```text
STATUS: DONE
branch: <branch>
worktree: <path>
commit: <hash>
tests:
- <command/result>
risks:
- <item>
handoff:
- <path>
```

## Sprint-Batch Close Checklist

Before closing cycle:

1. All selected thread issues are `Done`.
2. Integration issue is `Done` with verification results.
3. Retrospective issue is `Done`.
4. Repo artifacts exist:
- `sprints/<sprint>/SPRINT_LOG.md`
- `sprints/<sprint>/RETROSPECTIVE.md`
- `sprints/<sprint>/thread-reflections/*`
5. `docs/process/ROADMAP_BACKLOG.md` is re-ranked.

## Continuous Improvement Loop

Every two sprints:

1. Review Linear metrics:
- blocked duration
- integration conflict rate
- re-opened issues

2. Update this document with process changes.

3. Record improvements as explicit backlog items in `docs/process/ROADMAP_BACKLOG.md`.

4. Run maintenance threads (project organizer + code refactorer) using:
- `docs/process/MAINTENANCE_THREADS.md`

## Live Workspace Snapshot

Initialized on: 2026-02-24

- Team: `AutoApply` (`AUT`)
- Project: `AutoApply`
- Project URL: `https://linear.app/autoapplyps/project/autoapply-98ed9b02fe28`

Implemented setup from repo docs:

1. Sprint 05 historical issues created and marked `Done`:
- `AUT-5` through `AUT-10`
- Includes dependency chain:
  - `AUT-9` blocked by `AUT-5`, `AUT-6`, `AUT-7`, `AUT-8`
  - `AUT-10` blocked by `AUT-9`

2. Backlog queue currently includes:
- historical series `AUT-11` through `AUT-20`
- MVP refocus series `AUT-28` through `AUT-33`
- Status set to `Backlog` for future sprint-batch selection.

3. Label set created for this workflow:
- `sprint-05`, `quality`, `llm`, `capture`, `ux`, `parser`, `integration`, `retrospective`, `cleanup`
- MVP labels: `mvp-p0`, `mvp-p1`, `post-mvp`
- Default Linear labels retained: `Feature`, `Bug`, `Improvement`
- Feature-group labels added:
  - `fg-core-reliability`
  - `fg-llm-intelligence`
  - `fg-user-experience`
  - `fg-platform-ops`
  - `fg-advanced-product`

Cycle note:
- MCP currently exposes cycle listing, but not cycle creation in this workflow.
- Use sprint labels (`sprint-XX`) + project/milestones as the sprint grouping mechanism until cycle creation is automated.
