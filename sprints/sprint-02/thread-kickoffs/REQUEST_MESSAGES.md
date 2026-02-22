# Sprint 02 New Thread Messages

Use brand-new threads for Sprint 02. Do not reuse Sprint 1 threads.

## S2-A Platform/API

```text
Sprint 2 kickoff.

Work only in your assigned Sprint 2 worktree and branch `codex/s2-platform-api`.
Do not use previous sprint threads or branches.
Sprint trunk is `codex/integration`; your branch will be merged into that trunk.

Read and follow:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/SAFETY_COMPLIANCE.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/PLAN.md

Implement only S2-A scope:
- GET /api/v1/applications
- GET /api/v1/applications/{id}
- PATCH /api/v1/applications/{id}/status
- GET /api/v1/applications/{id}/resume-versions
- GET /api/v1/resume-versions/{id}
- POST /api/v1/resume-versions/{id}/approve

Rules:
- No contract changes unless proposed and blocked.
- Keep responses/error semantics contract compliant.
- Commit frequently (after each logical unit), not as a single final commit.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/handoffs/S2-A.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- commit hash
- tests run/results
- assumptions/risks
```

## S2-B Compliance Runtime

```text
Sprint 2 kickoff.

Work only in your assigned Sprint 2 worktree and branch `codex/s2-compliance-runtime`.
Do not use previous sprint threads or branches.
Sprint trunk is `codex/integration`; your branch will be merged into that trunk.

Read and follow:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/SAFETY_COMPLIANCE.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/PLAN.md

Implement only S2-B scope:
- Wire compliance/approval logic into active backend runtime.
- Enforce 422/409/404 semantics with no bypass path.
- Add tests proving enforcement in live API path.

Rules:
- No contract changes unless proposed and blocked.
- Preserve truth-bound and approval-gate invariants.
- Commit frequently (after each logical unit), not as a single final commit.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/handoffs/S2-B.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- commit hash
- tests run/results
- assumptions/risks
```

## S2-C Package Layout

```text
Sprint 2 kickoff.

Work only in your assigned Sprint 2 worktree and branch `codex/s2-package-layout`.
Do not use previous sprint threads or branches.
Sprint trunk is `codex/integration`; your branch will be merged into that trunk.

Read and follow:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/architecture/BUILD_CONTRACT.md
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/PLAN.md

Implement only S2-C scope:
- Unify Python package layout to one canonical root.
- Remove import ambiguity between `autoapply/` and `src/autoapply`.
- Update imports/tests/entrypoints accordingly.

Rules:
- No behavioral changes outside import/package/runtime unification.
- If package move impacts contract behavior, stop and report.
- Commit frequently (after each logical unit), not as a single final commit.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/handoffs/S2-C.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- commit hash
- tests run/results
- assumptions/risks
```

## S2-D Repo Hygiene

```text
Sprint 2 kickoff.

Work only in your assigned Sprint 2 worktree and branch `codex/s2-repo-hygiene`.
Do not use previous sprint threads or branches.
Sprint trunk is `codex/integration`; your branch will be merged into that trunk.

Read and follow:
- /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/PLAN.md

Implement only S2-D scope:
- Add/update .gitignore.
- Remove generated/vendor artifacts from tracking.
- Document runtime/tooling baseline and canonical test commands.

Rules:
- No feature changes.
- Keep cleanup scoped and reviewable.
- Commit frequently (after each logical unit), not as a single final commit.

At completion write:
/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/sprints/sprint-02/handoffs/S2-D.md

Include:
- STATUS: DONE or STATUS: BLOCKED
- branch
- commit hash
- tests run/results
- assumptions/risks
```
