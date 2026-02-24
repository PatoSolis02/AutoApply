# Sprint 05 Plan

Date: 2026-02-24  
Mode: Parallel thread-batch (4 implementation threads)  
Owner: Integration/Product (`codex/integration`)

## Sprint Definition (This Project)

Sprint 05 is a thread batch: selected non-overlapping threads run in parallel, then integrate, recap, and re-rank backlog.

## Selected Backlog Items

- `Q-1` Resume parsing field accuracy (Priority 1)
- `B-1` PDF extraction edge-case fixes (Priority 1)
- `F-1` LLM provider integration foundation (Priority 1)
- `Q-2` LinkedIn capture reliability hardening (Priority 2)
- `Q-3` Human-friendly UI/navigation improvements (Priority 2)

Deferred to next batch:

- `Q-4`, `F-2`, `F-3`, `C-1`, `C-2` (dependent on Sprint 05 foundations and stability)

## Why This Batch

- Covers highest-priority items first.
- Preserves no-overlap ownership boundaries.
- Maximizes parallelism without high merge conflict risk.
- Produces user-visible demo outcomes (capture reliability + UX + parser quality).

## Workstreams

### S5-A Resume Parser Quality and PDF Robustness

Branch: `codex/s5-parser-quality`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_a_parser_quality`

Backlog IDs:

- `Q-1`, `B-1`

Primary ownership:

- `backend/app/resume_ingest.py`
- `backend/tests/test_resume_ingest.py`
- parser-specific fixtures/utilities

Out of scope:

- extension capture changes
- UI navigation work
- full LLM-driven parsing logic (that is future `F-2`)

### S5-B Capture Reliability

Branch: `codex/s5-capture-reliability`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_b_capture_reliability`

Backlog IDs:

- `Q-2`

Primary ownership:

- `extension/content.js`
- `extension/popup.js`
- capture-related extension tests

Out of scope:

- resume parser internals
- profile UX/navigation redesign
- backend parser contract changes

### S5-C UX and Navigation

Branch: `codex/s5-ux-navigation`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_c_ux_navigation`

Backlog IDs:

- `Q-3`

Primary ownership:

- `src/components/*` (navigation/layout)
- `src/pages/*` (workflow usability improvements)
- `src/styles.css`

Out of scope:

- extension capture logic
- parser internals
- LLM backend integration

### S5-D LLM Foundation (No Feature Coupling)

Branch: `codex/s5-llm-foundation`  
Worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_d_llm_foundation`

Backlog IDs:

- `F-1`

Primary ownership:

- new backend LLM provider abstraction/config modules
- environment/config docs for provider enablement
- tests for provider selection/fallback behavior

Out of scope:

- direct replacement of current generation/parser behavior
- frontend UX changes
- capture extension changes

## Worktree and Branch Rules

1. Every thread must use its own branch and worktree.
2. If branch/worktree exists, reuse it; otherwise create from `codex/integration`.
3. Do not run two active threads in the same worktree path.
4. Validate uniqueness before kickoff with `git worktree list`.

## Merge Order

1. `S5-D` (LLM foundation contracts and config baseline)
2. `S5-A` (parser quality)
3. `S5-B` (capture reliability)
4. `S5-C` (UX/navigation)
5. Integration verification pass

## Required Handoff Format

Each thread handoff must include:

- `STATUS: DONE` or `STATUS: BLOCKED`
- branch name
- worktree path
- final commit hash
- tests/checks run + summarized results
- assumptions/risks
- explicit contract notes (if any)

Handoff files:

- `sprints/sprint-05/handoffs/S5-A.md`
- `sprints/sprint-05/handoffs/S5-B.md`
- `sprints/sprint-05/handoffs/S5-C.md`
- `sprints/sprint-05/handoffs/S5-D.md`
