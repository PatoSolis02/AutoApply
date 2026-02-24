# Sprint 05 Linear Issue Set

Source of truth used:

- `docs/process/ROADMAP_BACKLOG.md`
- `docs/process/PARALLEL_WORKSTREAMS.md`
- `sprints/sprint-05/PLAN.md`

## Linear Setup (Sprint 05)

Project: `AutoApply`  
Cycle: `Sprint 05`  
Team: your active Linear team  

Recommended labels:

- `sprint-05`
- `quality`
- `bug`
- `feature`
- `llm`
- `capture`
- `ux`
- `parser`
- `integration`
- `retrospective`

Priority mapping (from repo backlog):

- Repo `1` -> Linear `Urgent`
- Repo `2` -> Linear `High`
- Repo `3` -> Linear `Medium`
- Repo `4` -> Linear `Low`
- Repo `5` -> Linear `No priority`

## Issues To Create

1. `S5-D LLM provider foundation (F-1)`
- Priority: `Urgent`
- Labels: `sprint-05`, `feature`, `llm`
- Branch: `codex/s5-llm-foundation`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_d_llm_foundation`
- Handoff: `sprints/sprint-05/handoffs/S5-D.md`
- Description:
  - Implement provider abstraction/config for LLM access.
  - Add deterministic fallback behavior when LLM is unavailable.
  - Add prompt/version contract docs and tests.
  - Out of scope: replacing current parser/generator behavior.

2. `S5-A Resume parser accuracy and PDF robustness (Q-1, B-1)`
- Priority: `Urgent`
- Labels: `sprint-05`, `quality`, `bug`, `parser`
- Branch: `codex/s5-parser-quality`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_a_parser_quality`
- Handoff: `sprints/sprint-05/handoffs/S5-A.md`
- Description:
  - Improve extraction accuracy for personal info, experience/jobs, and skills.
  - Resolve remaining PDF edge cases.
  - Add regression tests for real-world PDF patterns.
  - Keep response semantics stable (`200/400/415/422`).

3. `S5-B LinkedIn capture reliability hardening (Q-2)`
- Priority: `High`
- Labels: `sprint-05`, `quality`, `capture`
- Branch: `codex/s5-capture-reliability`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_b_capture_reliability`
- Handoff: `sprints/sprint-05/handoffs/S5-B.md`
- Description:
  - Harden extraction across list/detail/right-panel variants.
  - Reduce missing required field failures.
  - Add deterministic extractor tests.

4. `S5-C Human-friendly navigation and UX improvements (Q-3)`
- Priority: `High`
- Labels: `sprint-05`, `quality`, `ux`
- Branch: `codex/s5-ux-navigation`
- Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_c_ux_navigation`
- Handoff: `sprints/sprint-05/handoffs/S5-C.md`
- Description:
  - Improve navigation clarity and workflow guidance.
  - Improve labels, validation guidance, and error recovery messaging.
  - Keep design language consistent with current app.

5. `S5-INT Integrate Sprint 05 handoffs into codex/integration`
- Priority: `Urgent`
- Labels: `sprint-05`, `integration`
- Owner: Integration/Product thread
- Description:
  - Merge thread branches using sprint merge order.
  - Resolve conflicts while preserving contract compatibility.
  - Run full verification suite on `codex/integration`.
  - Publish integration summary.

6. `S5-RETRO Sprint 05 recap and backlog rerank`
- Priority: `High`
- Labels: `sprint-05`, `retrospective`
- Owner: Integration/Product thread
- Description:
  - Collect thread reflections.
  - Write sprint recap artifacts.
  - Update roadmap ordering for next sprint batch.

## Dependencies

Set these in Linear:

- `S5-INT` blocked by: `S5-A`, `S5-B`, `S5-C`, `S5-D`
- `S5-RETRO` blocked by: `S5-INT`

## Status Flow

Recommended status transitions:

1. `Todo` -> issue drafted, branch/worktree not started
2. `In Progress` -> thread is actively coding
3. `In Review` -> handoff file complete, waiting for integration
4. `Done` -> merged into `codex/integration` and verified

## Required Comment Template (Thread Completion)

Copy into Linear issue comment when a thread finishes:

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
- sprints/sprint-05/handoffs/<file>.md
```
