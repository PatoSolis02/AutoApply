# Sprint 07 Retrospective

Date closed: 2026-02-25  
Project: AutoApply (local-first MVP)  
Sprint type: LLM generation delivery + runtime quality hardening

## Sprint Goal

Deliver the selected Sprint 07 Linear scope:

- `AUT-15` LLM-based tailored resume generation
- `AUT-16` Technical debt cleanup in parser and runtime plumbing
- `AUT-23` Test runtime resource warning cleanup

## Delivery Model

- Sprint selected from Linear backlog using `sprint-07` label and status workflow.
- Parallel execution in isolated worktrees and dedicated branches.
- Integration performed on `codex/integration` with planned merge ordering.

## What Was Delivered

LLM generation (`AUT-15`):

- integrated LLM-assisted tailoring into resume generation pipeline
- deterministic fallback preserved for disabled/unavailable/provider-error paths
- LLM edits constrained to source-backed bullet rewording, preserving claims-map traceability
- approval/compliance gates unchanged and regression-tested

Runtime/parser cleanup (`AUT-16`):

- removed duplicated normalization merge scaffolding in resume ingest paths
- centralized assignment helper semantics for safer merge behavior
- simplified runtime fallback plumbing in LLM runtime layer
- added focused regression coverage for touched paths

Resource warning cleanup (`AUT-23`):

- explicit sqlite connection close lifecycle added for runtime DB operations
- warning-prone direct test sqlite usage wrapped with explicit close handling
- lifecycle tests added; backend suite validated under `ResourceWarning`-as-error mode

## Validation Summary

Integration verification passed:

1. backend test suite: `57` tests passed (with `PYTHONWARNINGS=error::ResourceWarning`)
2. root python tests: `25` tests passed
3. frontend tests: `29` tests passed
4. frontend build: pass

## What Went Well

1. Workstream boundaries were clear enough to merge all Sprint 07 threads without conflicts.
2. Merge order was effective: runtime lifecycle hygiene first, then cleanup refactor, then feature layer.
3. LLM feature delivery kept deterministic safety fallback and contract compatibility intact.
4. Thread handoffs included concrete commit/test evidence, speeding integration decisions.

## What Went Wrong

1. Runtime quality improvements landed, but generated content quality remains dependent on provider behavior and prompt tuning not yet benchmarked.
2. Parser/runtime modules are still larger than ideal, which keeps long-term maintenance pressure high.
3. Resume extraction robustness still has edge PDFs that can fail text extraction in manual usage.

## Root Causes

1. LLM foundation intentionally prioritized reliability contracts over quality-eval instrumentation.
2. Parser/runtime code has accumulated responsibilities across several sprint batches.
3. Resume extraction relies on heterogeneous PDF structures with inconsistent text-layer quality.

## Key Learnings

1. Constraining LLM output to source-backed transformations is practical for safety while still adding product value.
2. Escalating resource warnings to hard errors is effective for preventing runtime hygiene regressions.
3. Parallel lane decomposition works best when contracts are fixed and shared module edits are explicitly scoped.
4. Integration notes and reflection artifacts should be treated as first-class outputs, not optional docs.

## Action Items

Process:

1. Continue mandatory Linear state progression (`Todo` -> `In Progress` -> `In Review` -> `Done`) per thread.
2. Keep integration comments in Linear with merge hashes and verification outcomes for each sprint close.
3. Maintain sprint close bar: `SPRINT_LOG.md`, `RETROSPECTIVE.md`, thread reflections, and backlog rerank.

Technical:

1. Add generation quality evaluation fixtures for factual consistency and relevance scoring.
2. Continue incremental parser/runtime decomposition in targeted, low-overlap threads.
3. Track and harden remaining PDF extraction edge cases with representative fixture coverage.

## Every-Two-Sprints Maintenance Trigger

Sprint 07 is not a maintenance-boundary sprint.  
Next mandatory maintenance boundary is Sprint 08 (project organizer + code refactorer threads).

Canonical prompts are in:

- `docs/process/MAINTENANCE_THREADS.md`

## Current Standing

Sprint 07 outcome: **completed and integrated**.

Current active backlog for next sprint selection is now centered on:

- `AUT-17` advanced audit export for larger histories
- `AUT-18` fit scoring and gap analysis
- `AUT-19` packaging and release documentation hardening
- `AUT-20` non-critical refactor and polish cleanup
