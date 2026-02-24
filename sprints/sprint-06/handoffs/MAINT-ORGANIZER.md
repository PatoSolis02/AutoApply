STATUS: DONE

branch: `codex/maint-project-organizer`
worktree path: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_maint_project_organizer`
final commit hash: `ab1a602` (maintenance structure changeset; handoff metadata committed afterward)

scope delivered:
1. Reorganized process documentation entrypoints for discoverability:
- Added `docs/process/README.md` as the canonical process index.
- Clarified active process docs vs archived/legacy docs.
2. Consolidated stale kickoff process docs without breaking legacy references:
- Moved legacy generic template to `docs/process/archive/THREAD_KICKOFFS_LEGACY_WS.md`.
- Replaced `docs/process/THREAD_KICKOFFS.md` with a redirect note to current sprint kickoffs and maintenance kickoff sources.
3. Normalized maintenance kickoff instructions for path clarity:
- Updated `docs/process/MAINTENANCE_THREADS.md` to reference `docs/process/README.md` and `docs/process/ROADMAP_BACKLOG.md` explicitly.
- Updated one ambiguous backlog path reference in `docs/process/LINEAR_WORKFLOW.md`.
4. Improved Sprint 06 artifact discoverability and predictable folder navigation:
- Added `sprints/sprint-06/README.md`.
- Added `sprints/sprint-06/handoffs/README.md`.
- Added `sprints/sprint-06/thread-reflections/README.md`.
- Added `sprints/sprint-06/thread-kickoffs/README.md`.

runtime behavior impact:
- No runtime product behavior changes.
- No backend/frontend/application logic changes.

checks run + results:
1. `python3 scripts/check_tracked_artifacts.py`
- PASS: `Tracked artifact/vendor check passed: no blocked files are tracked.`
2. `python3 scripts/check_runtime_versions.py`
- PARTIAL/ENV FAIL: python runtime in environment is `3.9.6`, below baseline `>=3.11.x`.
- Node/npm baseline checks passed.
3. Reference sanity check:
- `rg -n "docs/process/THREAD_KICKOFFS\.md|docs/process/archive/THREAD_KICKOFFS_LEGACY_WS\.md|docs/process/README\.md" docs sprints`
- PASS: expected references resolve to existing process docs/redirects.

residual risks:
1. Some historical sprint artifacts still reference `docs/process/THREAD_KICKOFFS.md`; they now resolve via redirect note, but not all historical text has been modernized to sprint-specific kickoff artifacts.
2. Runtime baseline check cannot fully pass in this environment until Python `3.11.x` is selected.
3. No markdown linting/check tooling was executed (repo does not currently define a canonical markdown lint command in process docs).
