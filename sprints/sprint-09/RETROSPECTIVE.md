# Sprint 09 Retrospective

Date closed: 2026-02-25  
Project: AutoApply (local-first MVP)  
Sprint type: MVP foundation hardening (auth + capture + format contract)

## Sprint Goal

Deliver the selected Sprint 09 Linear scope:

- `AUT-34` Auth backend session and token contract
- `AUT-32` Real-job capture reliability hardening for MVP
- `AUT-37` Generation format contract using redacted resume baseline

## Delivery Model

- Sprint selected from Linear backlog using `sprint-09` label and status workflow.
- Parallel execution in isolated worktrees and dedicated branches.
- Integration performed on `codex/integration` with planned merge ordering.

## What Was Delivered

Auth backend contract (`AUT-34`):

- backend signup/login/logout/session endpoints implemented
- deterministic auth/session error semantics and codes
- session expiry and revocation behavior enforced
- auth persistence tables and contract tests added

Capture reliability (`AUT-32`):

- LinkedIn extraction fallback logic hardened for multiple layout variants
- required-field fallback behavior improved for real-page variance
- field-specific recovery guidance added in extension and capture UI
- deterministic extractor/capture regression fixtures expanded

Generation format contract (`AUT-37`):

- versioned generated resume contract (`resume_format.v1`) introduced
- explicit section ordering/label rules and baseline anchor added
- runtime conformance checks enforced before artifact write
- generation contract documentation and tests added

## Validation Summary

Integration verification passed:

1. backend test suite: `73` tests passed
2. root python tests: `29` tests passed
3. frontend tests: `33` tests passed
4. frontend build: pass

## What Went Well

1. Workstream boundaries were concrete and file overlap stayed low, resulting in clean merges.
2. Contract-first handoffs reduced ambiguity during integration decisions.
3. Planned merge ordering matched dependency reality and avoided rework.
4. Verification coverage across backend and frontend remained stable after all merges.

## What Went Wrong

1. Sprint recap artifacts were not created immediately after integration and had to be completed as follow-up.
2. Sprint 08 recap issue (`AUT-27`) remains open, showing recap hygiene drift across sprints.
3. Full-suite backend test output is increasingly verbose, which slows manual verification review.

## Root Causes

1. Integration close checklist enforcement focused on merges/tests but not on immediate recap artifact generation.
2. Recap ownership was implicitly distributed and not treated as a strict integration-owner responsibility.
3. Structured observability output has grown without a concise test-mode output path.

## Key Learnings

1. Recap ownership must remain with integration/product lane every sprint, without exception.
2. Contract-split story decomposition continues to scale well for parallel thread execution.
3. Explicit close criteria should include both Linear state updates and recap file presence checks.
4. Sprint-level backlog rerank is most effective when tied directly to MVP gates, not broad feature lists.

## Action Items

Process:

1. Keep recap generation (`SPRINT_LOG.md`, `RETROSPECTIVE.md`) as mandatory integration close steps.
2. Add recap completion check into sprint close flow before marking recap issues done.
3. Close stale recap issue debt starting with `AUT-27`.

Technical:

1. Prioritize `AUT-35` and `AUT-36` to complete end-to-end authenticated MVP flow.
2. Prioritize `AUT-29` and `AUT-38` to complete ingest-to-generation value path.
3. Continue expanding capture fixtures for real LinkedIn DOM variants to preserve reliability gains.

## Every-Two-Sprints Maintenance Trigger

Sprint 09 is not a maintenance-boundary sprint.  
Next mandatory maintenance boundary is Sprint 10 (project organizer + code refactorer threads).

Canonical prompts are in:

- `docs/process/MAINTENANCE_THREADS.md`

## Current Standing

Sprint 09 outcome: **completed and integrated**.

Current active backlog for next sprint selection is now centered on:

- `AUT-35` auth UI flow and route protection
- `AUT-36` per-user data scoping for profile and applications
- `AUT-29` resume ingest to profile auto-fill with editable sections
- `AUT-38` automatic profile evidence selection in generation runtime
- `AUT-31` application tracking core workflow hardening
