# Sprint 04 Thread Kickoff Messages

Use these prompts verbatim in new threads.

## S4-A Resume Ingestion Backend

```text
Sprint 4 kickoff.

Work only in branch `codex/s4-ingestion-backend` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s4_a_ingestion_backend

If worktree/branch do not exist, create them from `codex/integration`. If they already exist, reuse them.
Do not use old sprint branches.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-04/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/SAFETY_COMPLIANCE.md

Implement only S4-A scope:
- Resume upload parse pipeline for pdf/docx.
- API endpoint(s) for upload + parse output.
- Validation and mapping tests.

Rules:
- Keep parsed output contract explicit and documented in handoff.
- No unrelated frontend changes.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-04/handoffs/S4-A.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- commit hash
- tests/checks run + results
- assumptions/risks
```

## S4-B Profile Builder UX

```text
Sprint 4 kickoff.

Work only in branch `codex/s4-profile-ux` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s4_b_profile_ux

If worktree/branch do not exist, create them from `codex/integration`. If they already exist, reuse them.
Do not use old sprint branches.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-04/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md

Implement only S4-B scope:
- Structured profile editor UX as primary path.
- Upload-to-profile flow wired to S4-A API contract.
- JSON editing as advanced fallback only.

Rules:
- Do not redefine ingestion API contract without blocking handoff note.
- No unrelated backend refactors.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-04/handoffs/S4-B.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- commit hash
- tests/checks run + results
- assumptions/risks
```

## S4-C End-to-End Workflow and Audit Visibility

```text
Sprint 4 kickoff.

Work only in branch `codex/s4-workflow-audit` and worktree:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s4_c_workflow_audit

If worktree/branch do not exist, create them from `codex/integration`. If they already exist, reuse them.
Do not use old sprint branches.

Read:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-04/PLAN.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md

Implement only S4-C scope:
- End-to-end UI flow from capture to ready_to_apply.
- Improve claims/change-log visibility in review UI.
- Basic audit export/view capability.
- Add end-to-end acceptance coverage for intended workflow.

Rules:
- Consume S4-A/S4-B contracts; do not fork them.
- Keep work focused on workflow completeness and traceability.
- Commit after each logical unit.
- Only message when blocked.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-04/handoffs/S4-C.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- worktree path
- commit hash
- tests/checks run + results
- assumptions/risks
```
