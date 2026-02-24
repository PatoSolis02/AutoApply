# Linear Workflow Guide

Last updated: 2026-02-24
Owner: Integration/Product thread

## Purpose

This doc defines how AutoApply uses Linear for sprint-batch planning, execution tracking, integration, and retrospectives.

## Core Principle

Use Linear as the execution control plane; use git/worktrees as the implementation plane.

- Linear tracks: priority, ownership, status, blockers, dependencies, recap.
- Git tracks: branches, commits, tests, integrations.

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

3. Record improvements as explicit backlog items in `ROADMAP_BACKLOG.md`.
