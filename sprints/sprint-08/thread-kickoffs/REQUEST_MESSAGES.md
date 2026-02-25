# Sprint 08 Thread Kickoff Messages

Copy/paste each block as the first message in a separate thread.

## Thread A (AUT-17): advanced audit export

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/architecture/SAFETY_COMPLIANCE.md, and sprints/sprint-08/PLAN.md.

You own Sprint 08 Thread A for Linear issue AUT-17: Advanced audit export for larger histories.

Create/reuse branch: codex/s8-a-audit-export
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_a_audit_export

Set AUT-17 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Implement robust large-history audit export behavior.
- Define and enforce explicit size/limit/failure behavior.
- Add regression tests for large-history and limit paths.

Out of scope:
- Fit scoring implementation (AUT-18).
- Release docs hardening (AUT-19).

Deliverables:
- Handoff: sprints/sprint-08/handoffs/S8-A.md
- Reflection: sprints/sprint-08/thread-reflections/S8-A.md
- Include commit hash, tests run, assumptions/risks, contract notes.
```

## Thread B (AUT-18): fit scoring and gap analysis

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/architecture/SAFETY_COMPLIANCE.md, and sprints/sprint-08/PLAN.md.

You own Sprint 08 Thread B for Linear issue AUT-18: Fit scoring and gap analysis.

Create/reuse branch: codex/s8-b-fit-scoring
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_b_fit_scoring

Set AUT-18 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Implement fit scoring and gap-analysis outputs.
- Keep output deterministic and test-covered for repeated inputs.
- Preserve existing compliance and approval invariants.

Out of scope:
- Audit export scalability implementation (AUT-17).
- Release docs hardening (AUT-19).

Deliverables:
- Handoff: sprints/sprint-08/handoffs/S8-B.md
- Reflection: sprints/sprint-08/thread-reflections/S8-B.md
- Include commit hash, tests run, assumptions/risks, contract notes.
```

## Thread C (AUT-19): packaging and release docs hardening

```text
Read docs/process/, docs/process/TOOLING_BASELINE.md, and sprints/sprint-08/PLAN.md.

You own Sprint 08 Thread C for Linear issue AUT-19: Packaging and release documentation hardening.

Create/reuse branch: codex/s8-c-release-docs
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s8_c_release_docs

Set AUT-19 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Standardize backend/frontend/extension packaging and release runbooks.
- Remove stale/contradictory release instructions.
- Validate runbook steps against current repository workflow.

Out of scope:
- Runtime feature implementation changes.
- Code refactor scope outside docs/process and release docs.

Deliverables:
- Handoff: sprints/sprint-08/handoffs/S8-C.md
- Reflection: sprints/sprint-08/thread-reflections/S8-C.md
- Include commit hash, checks run, assumptions/risks, behavior-preservation statement.
```

## Completion Signal

When all sprint threads are done, send:

`All Sprint 8 handoffs and retrospectives ready. Integrate from codex/integration.`
