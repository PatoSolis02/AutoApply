# Sprint 03 Thread Kickoff Messages

Use these prompts verbatim in new threads.

## S3-A CI and Guardrails

```text
Sprint 3 kickoff.

Work only in branch `codex/s3-ci-guardrails` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s3_a_ci_guardrails

If worktree/branch do not exist, create them from `codex/integration`. If they already exist, reuse them.
Do not use old sprint branches.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-03/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/process/TOOLING_BASELINE.md

Implement only S3-A scope:
- CI pipeline for backend/frontend test + build.
- Runtime version enforcement.
- Hygiene checks to block tracked generated/vendor artifacts.

Rules:
- No feature behavior changes.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-03/handoffs/S3-A.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- commit hash
- tests/checks run + results
- assumptions/risks
```

## S3-B Backend Contract Reliability

```text
Sprint 3 kickoff.

Work only in branch `codex/s3-backend-reliability` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s3_b_backend_reliability

If worktree/branch do not exist, create them from `codex/integration`. If they already exist, reuse them.
Do not use old sprint branches.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-03/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/SAFETY_COMPLIANCE.md

Implement only S3-B scope:
- Approval/status coupling tests (including idempotency).
- /api/v1/profile edge-case contract tests.
- Add GET /health endpoint.
- Keep explicit contract error semantics.

Rules:
- No unrelated refactors.
- No contract changes unless blocked and documented.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-03/handoffs/S3-B.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- commit hash
- tests/checks run + results
- assumptions/risks
```

## S3-C Capture and Frontend Reliability

```text
Sprint 3 kickoff.

Work only in branch `codex/s3-capture-frontend-reliability` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s3_c_capture_frontend_reliability

If worktree/branch do not exist, create them from `codex/integration`. If they already exist, reuse them.
Do not use old sprint branches.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-03/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md

Implement only S3-C scope:
- LinkedIn extractor fixture tests for DOM variants.
- Frontend /profile tests (load/save/error/JSON validation).
- Lightweight diagnostics panel in UI using backend health/status signals.

Rules:
- No backend contract changes (consume existing/approved APIs).
- Keep UI additions minimal and operational.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-03/handoffs/S3-C.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- commit hash
- tests/checks run + results
- assumptions/risks
```
