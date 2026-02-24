# Maintenance Threads (Every Two Sprints)

Last updated: 2026-02-24
Owner: Integration/Product thread

## Trigger Rule

At every second sprint close (Sprint 2, 4, 6, ...), run both maintenance threads in parallel:

1. Project organizer thread
2. Code refactorer thread

Do this after sprint integration is complete and before selecting the next sprint batch.

## Worktree Requirement

Each maintenance thread must use a separate branch and worktree created from `codex/integration`.

## Kickoff Message: Project Organizer Thread

```text
Read docs/process/, ROADMAP_BACKLOG.md, and current sprint artifacts. You own the Project Organizer maintenance lane.

Create/reuse branch: codex/maint-project-organizer
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_maint_project_organizer

Scope:
- Reorganize docs/process and sprint artifacts for clarity and discoverability.
- Remove stale/duplicate process docs or consolidate with redirects/notes.
- Ensure naming and folder structure remain consistent and predictable.
- Do not change runtime product behavior.

Deliver:
- Commit(s) on codex/maint-project-organizer
- Handoff file: sprints/<current-sprint>/handoffs/MAINT-ORGANIZER.md
- Thread reflection: sprints/<current-sprint>/thread-reflections/MAINT-ORGANIZER.md
- Include tests/checks run (if any) and residual risks.
```

## Kickoff Message: Code Refactorer Thread

```text
Read docs/process/, architecture contracts, and current sprint artifacts. You own the Code Refactorer maintenance lane.

Create/reuse branch: codex/maint-code-refactor
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_maint_code_refactor

Scope:
- Simplify and refactor code paths for readability and traceability.
- Preserve behavior and public contracts; no feature scope expansion.
- Prioritize high-friction complexity in parser/runtime/frontend glue code.
- Add or adjust tests where refactors need regression protection.

Deliver:
- Commit(s) on codex/maint-code-refactor
- Handoff file: sprints/<current-sprint>/handoffs/MAINT-REFACTOR.md
- Thread reflection: sprints/<current-sprint>/thread-reflections/MAINT-REFACTOR.md
- Include tests/checks run and explicit statement of behavior preservation.
```

## Integration Checklist

1. Merge organizer lane first (structure/docs).
2. Merge refactor lane second.
3. Run full verification on `codex/integration`.
4. Record outcomes in sprint log and retrospective.
