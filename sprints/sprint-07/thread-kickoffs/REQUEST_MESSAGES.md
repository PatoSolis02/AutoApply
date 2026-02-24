# Sprint 07 Thread Kickoff Messages

Copy/paste each block as the first message in a separate thread.

## Thread A (AUT-15): LLM tailored resume generation

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, docs/architecture/SAFETY_COMPLIANCE.md, and sprints/sprint-07/PLAN.md.

You own Sprint 07 Thread A for Linear issue AUT-15: LLM-based tailored resume generation.

Create/reuse branch: codex/s7-a-llm-generation
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s7_a_llm_generation

Set AUT-15 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Implement LLM-driven resume generation from job content + user profile.
- Preserve compliance gates, claims mapping, and approval workflow behavior.
- Add contract tests for success/failure/fallback generation paths.

Out of scope:
- Parser/runtime technical debt refactors.
- SQLite warning cleanup work.

Deliverables:
- Handoff: sprints/sprint-07/handoffs/S7-A.md
- Reflection: sprints/sprint-07/thread-reflections/S7-A.md
- Include commit hash, tests run, assumptions/risks, contract notes.
```

## Thread B (AUT-16): parser/runtime technical debt cleanup

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, and sprints/sprint-07/PLAN.md.

You own Sprint 07 Thread B for Linear issue AUT-16: Technical debt cleanup in parser and runtime plumbing.

Create/reuse branch: codex/s7-b-runtime-cleanup
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s7_b_runtime_cleanup

Set AUT-16 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Simplify parser/runtime plumbing for readability and traceability.
- Reduce brittle/duplicated code paths while preserving behavior/contracts.
- Add regression tests for touched modules.

Out of scope:
- LLM generation feature expansion (AUT-15).
- SQLite warning cleanup ownership (AUT-23).

Deliverables:
- Handoff: sprints/sprint-07/handoffs/S7-B.md
- Reflection: sprints/sprint-07/thread-reflections/S7-B.md
- Include commit hash, tests run, assumptions/risks, behavior-preservation statement.
```

## Thread C (AUT-23): runtime resource warning cleanup

```text
Read docs/process/, docs/architecture/BUILD_CONTRACT.md, and sprints/sprint-07/PLAN.md.

You own Sprint 07 Thread C for Linear issue AUT-23: Test runtime resource warning cleanup.

Create/reuse branch: codex/s7-c-runtime-warning-cleanup
Create/reuse worktree: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s7_c_runtime_warning_cleanup

Set AUT-23 to In Progress once branch/worktree is ready. Set to In Review when handoff is complete.

Scope:
- Eliminate recurring sqlite ResourceWarning noise in backend test/runtime flows.
- Ensure connection lifecycle cleanup is explicit and test-verified.
- Keep runtime behavior and API contracts unchanged.

Out of scope:
- Feature work.
- Broad parser/runtime cleanup outside warning-source paths.

Deliverables:
- Handoff: sprints/sprint-07/handoffs/S7-C.md
- Reflection: sprints/sprint-07/thread-reflections/S7-C.md
- Include commit hash, tests run, assumptions/risks, warning delta evidence.
```

## Completion Signal

When all sprint threads are done, send:

`All Sprint 7 handoffs and retrospectives ready. Integrate from codex/integration.`
