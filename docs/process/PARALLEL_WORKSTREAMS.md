# AutoApply Parallel Workstream Plan

## Operating Model

- Single architecture owner: this thread.
- Parallel implementation: separate execution threads per workstream.
- Integration authority: this thread enforces `docs/architecture/BUILD_CONTRACT.md`.
- Use as many threads as makes sense only when work can be partitioned into non-overlapping ownership boundaries.
- Avoid overlapping parallel work: if two scopes touch the same primary files/contracts, keep them in one thread or run sequentially.

## Threading Policy (Current)

1. Maximize parallelism where ownership is independent; do not force a fixed thread count.
2. Before kickoff, create a file/path ownership map per thread.
3. One task has one owner thread; no dual ownership.
4. Contract changes must be proposed to integration owner before implementation in parallel threads.
5. Integration owner merges by dependency order and is final conflict resolver.

## Git Worktree Requirement (Parallel Safety)

- Every active implementation thread must run in its own git worktree.
- Do not run multiple active threads in the same working directory.
- Each worktree maps to exactly one branch and one thread owner.

Recommended setup pattern:

1. Create branch from integration:
- `git checkout -b codex/<thread-branch-name> codex/integration`

2. Add worktree for the thread:
- `git worktree add /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/<thread-name> codex/<thread-branch-name>`

3. Execute thread work only inside that worktree path.

4. Remove worktree after integration:
- `git worktree remove /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/<thread-name>`

Naming convention:

- Branch: `codex/<topic>-<scope>`
- Worktree folder: `autoapply_<topic>_<scope>`

Validation rule:

- Before kickoff, run `git worktree list` and confirm each active thread has a unique path and branch.

## Sprint Definition (Thread-Batch Model)

In this project, a sprint is not primarily a time box.  
A sprint is a selected batch of parallel threads that can run together without overlap, then integrate, recap, and repeat.

Sprint lifecycle:

1. Select thread batch from backlog by MVP gate (`docs/process/MVP_SCOPE.md`) + dependency readiness.
2. Launch all non-overlapping threads in parallel (each in separate worktree).
3. Integrate all completed thread handoffs into `codex/integration`.
4. Run recap/retrospective and update backlog ordering.
5. Start next sprint batch from the updated queue.

## Workstream Design (Generic)

For every sprint batch, define workstreams from current backlog items (do not reuse old WS scopes by default).

Use this template per workstream:

1. Workstream ID and name
2. Goal (single primary objective)
3. In-scope tasks (exact backlog IDs)
4. Out-of-scope boundaries
5. Owned files/directories
6. Contract dependencies
7. Deliverables
8. Required tests/checks
9. Handoff file path

Recommended workstream types (choose only what applies for the sprint batch):

- Quality and bug-fix lane
- Frontend UX/navigation lane
- Backend feature lane
- LLM/platform lane
- QA/observability lane
- Cleanup/technical-debt lane

## Thread Batch Planning Algorithm

Use this algorithm each sprint to decide which parallel threads run together:

1. Start from highest-priority ready MVP items (`MVP-P0` then `MVP-P1`).
2. Group tasks by ownership boundary (files/contracts), not by equal workload.
3. Split into separate threads only when overlap is low.
4. Keep overlapping tasks in one thread or sequence them in a later batch.
5. Stop adding threads when integration complexity outweighs parallel speed.

Thread batch guardrails:

- Usually run 3-5 threads in parallel.
- Expand above 5 only with very clean ownership boundaries.
- Each thread should have one primary objective.
- Keep 20-30% of batch capacity for regressions/hotfixes.

## Integration Sequence (Generic)

1. Merge contract and foundation changes first.
2. Merge dependent feature lanes second.
3. Merge UX wiring after dependent API/contracts are stable.
4. Merge test/observability and docs updates.
5. Run full verification on `codex/integration`.

If conflicts appear:

1. Integration owner resolves conflicts on `codex/integration`.
2. Preserve contract compatibility first, then feature completeness.
3. Re-run full test suite before declaring integration complete.

## Branching Conventions (Generic)

- Branch format: `codex/<topic>-<scope>`
- One branch per thread, one worktree per branch.
- Every thread handoff must include:
  - commit hash
  - tests run and outcomes
  - open risks/assumptions
  - explicit contract notes

## Drift Control

If a workstream needs contract changes:

1. Stop coding that part.
2. Propose contract delta in this thread.
3. Update `docs/architecture/BUILD_CONTRACT.md`.
4. Resume implementation only after contract update.

## Definition of Done (Program-Level)

1. All selected sprint-batch workstreams merged into `codex/integration` without unresolved contract conflicts.
2. Required tests for all selected backlog items pass on integration branch.
3. Critical user flows impacted by the sprint batch pass smoke validation.
4. Compliance rules from `docs/architecture/SAFETY_COMPLIANCE.md` remain enforced in code and tests.
5. Sprint artifacts are complete (handoffs, reflections, recap, backlog re-prioritization).
