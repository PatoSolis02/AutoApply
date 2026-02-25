# Sprint 09 Thread Kickoff Messages

Copy/paste each block as the first message in a separate thread.

## Thread A (AUT-34): auth backend session/token contract

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/process/MVP_SCOPE.md, and sprints/sprint-09/PLAN.md.

You own Sprint 09 Thread A for Linear issue AUT-34: Auth backend session and token contract.

Create/reuse branch: codex/s9-a-auth-backend
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_a_auth_backend

Set AUT-34 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Implement backend signup/login/logout/session primitives.
- Define deterministic auth/session error semantics and expiry behavior.
- Add backend contract tests for success/failure/expired session paths.

Out of scope:
- Frontend auth UI and route guards (AUT-35).
- Cross-user data migration/scoping work (AUT-36).

Deliverables:
- Handoff: sprints/sprint-09/handoffs/S9-A.md
- Reflection: sprints/sprint-09/thread-reflections/S9-A.md
- Include commit hash, tests run, assumptions/risks, contract notes.
```

## Thread B (AUT-32): capture reliability hardening

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/process/MVP_SCOPE.md, and sprints/sprint-09/PLAN.md.

You own Sprint 09 Thread B for Linear issue AUT-32: Real-job capture reliability hardening for MVP.

Create/reuse branch: codex/s9-b-capture-reliability
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_b_capture_reliability

Set AUT-32 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Improve extraction robustness for real target pages (LinkedIn-first).
- Harden required-field fallback behavior and user-facing recovery guidance.
- Add deterministic regression fixtures/tests for known DOM/layout variants.

Out of scope:
- Auth implementation scope.
- Resume generation format/template contract work.

Deliverables:
- Handoff: sprints/sprint-09/handoffs/S9-B.md
- Reflection: sprints/sprint-09/thread-reflections/S9-B.md
- Include commit hash, tests run, assumptions/risks, contract notes.
```

## Thread C (AUT-37): generation format contract baseline

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/process/MVP_SCOPE.md, and sprints/sprint-09/PLAN.md.

You own Sprint 09 Thread C for Linear issue AUT-37: Generation format contract using redacted resume baseline.

Create/reuse branch: codex/s9-c-generation-format-contract
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_c_generation_format_contract

Set AUT-37 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Define/version generated resume format contract and section ordering.
- Anchor baseline to artifacts/resume_samples/Redacted Resume.pdf.
- Add contract conformance checks/tests for generated output.

Out of scope:
- Automatic profile evidence selection runtime changes (AUT-38).
- Capture/auth feature changes.

Deliverables:
- Handoff: sprints/sprint-09/handoffs/S9-C.md
- Reflection: sprints/sprint-09/thread-reflections/S9-C.md
- Include commit hash, checks run, assumptions/risks, contract notes.
```

## Completion Signal

When all sprint threads are done, send:

`All Sprint 9 handoffs and retrospectives ready. Integrate from codex/integration.`
