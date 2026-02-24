# Sprint 05 Thread Kickoff Messages

Use each block as the first message in a separate thread.

## S5-A Resume Parser Quality and PDF Robustness

```text
Sprint 5 kickoff.

Work only in branch `codex/s5-parser-quality` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_a_parser_quality

If branch/worktree do not exist, create both from `codex/integration`. If they already exist, reuse them.
Before coding, run `git worktree list` and confirm no thread shares this path/branch.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/process/PARALLEL_WORKSTREAMS.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/SAFETY_COMPLIANCE.md

Implement only S5-A scope (`Q-1`, `B-1`):
- Improve extraction accuracy for personal info, experience/jobs, and skills.
- Fix residual PDF edge cases after hotfix.
- Add/expand regression tests for real-world PDF patterns.

Rules:
- Keep existing API status semantics stable (`200/400/415/422`).
- No extension capture changes.
- No UI/navigation changes.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/handoffs/S5-A.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- final commit hash
- tests/checks run + results
- assumptions/risks
- contract notes
```

## S5-B Capture Reliability

```text
Sprint 5 kickoff.

Work only in branch `codex/s5-capture-reliability` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_b_capture_reliability

If branch/worktree do not exist, create both from `codex/integration`. If they already exist, reuse them.
Before coding, run `git worktree list` and confirm no thread shares this path/branch.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/process/PARALLEL_WORKSTREAMS.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md

Implement only S5-B scope (`Q-2`):
- Harden LinkedIn capture extraction for list/detail/right-panel variants.
- Reduce missing required field failures.
- Add deterministic extractor tests for known layouts.

Rules:
- No resume parser internals.
- No UX navigation redesign.
- No backend contract changes without explicit blocker note.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/handoffs/S5-B.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- final commit hash
- tests/checks run + results
- assumptions/risks
- contract notes
```

## S5-C UX and Navigation

```text
Sprint 5 kickoff.

Work only in branch `codex/s5-ux-navigation` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_c_ux_navigation

If branch/worktree do not exist, create both from `codex/integration`. If they already exist, reuse them.
Before coding, run `git worktree list` and confirm no thread shares this path/branch.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/process/PARALLEL_WORKSTREAMS.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md

Implement only S5-C scope (`Q-3`):
- Make navigation and workflow UX more human-friendly.
- Improve labels, guidance, error recovery messaging, and click path efficiency.
- Keep design consistent with existing app style.

Rules:
- No capture extension logic.
- No parser internals.
- No LLM backend integration.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/handoffs/S5-C.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- final commit hash
- tests/checks run + results
- assumptions/risks
- contract notes
```

## S5-D LLM Foundation

```text
Sprint 5 kickoff.

Work only in branch `codex/s5-llm-foundation` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_d_llm_foundation

If branch/worktree do not exist, create both from `codex/integration`. If they already exist, reuse them.
Before coding, run `git worktree list` and confirm no thread shares this path/branch.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/process/PARALLEL_WORKSTREAMS.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/SAFETY_COMPLIANCE.md

Implement only S5-D scope (`F-1`):
- Add LLM provider integration foundation (config + provider abstraction + deterministic fallback).
- Add docs/contracts for prompt/version and fail-safe behavior.
- Add tests for provider selection and fallback behavior.

Rules:
- Do not replace current parser/generator behavior in this sprint.
- No frontend UX changes.
- Keep contracts additive and backward compatible.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-05/handoffs/S5-D.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- final commit hash
- tests/checks run + results
- assumptions/risks
- contract notes
```
