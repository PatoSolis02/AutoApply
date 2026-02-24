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

## Workstreams

### WS-A: Capture and Ingest

Scope:

- Chrome extension data extraction (title, company, location, URL, description).
- Backend endpoint `POST /api/v1/jobs/capture`.
- Validation and persistence for `Application` + `JobPosting`.

Out of scope:

- Resume generation, UI approval flow, fit scoring.

Deliverables:

- Extension capture action.
- Ingest API with tests.
- SQLite migrations for capture tables.

### WS-B: Dashboard and Application Tracking UI

Scope:

- Application list/detail views.
- Status transition UI with backend integration.
- Resume version list/detail read views.
- Approval action integration.

Out of scope:

- Resume generation algorithm internals.

Deliverables:

- React pages for list/detail/version timeline.
- Status and approval actions with optimistic or confirmed update behavior.
- Basic error states for `409` and `422`.

### WS-C: Tailoring and PDF Pipeline

Scope:

- Tailoring engine from `UserProfile` + `JobPosting`.
- HTML render model generation.
- PDF generation and artifact persistence.
- Endpoint `POST /api/v1/applications/{id}/resume-versions/generate`.

Out of scope:

- UI implementation details.

Deliverables:

- Deterministic render model output.
- HTML and PDF files saved per contract path rules.
- Unit tests for content selection logic.

### WS-D: Audit, Claims Mapping, and Compliance Gates

Scope:

- `change_log` and `claims_map` generation/validation.
- Compliance gating (`422` on unsupported claims).
- Version immutability checks.
- Approval gate behavior.

Out of scope:

- Extension and frontend page composition.

Deliverables:

- Claims verifier module.
- Audit metadata persistence.
- Compliance tests for rejection scenarios.

## Integration Sequence

1. Merge WS-A first.
2. Merge WS-C and WS-D next (order can vary).
3. Merge WS-B after APIs are stable enough for full wiring.
4. Final integration pass in architecture-owner thread.

## Branching and PR Conventions

- Branch prefixes:
  - `codex/ws-a-capture-ingest`
  - `codex/ws-b-dashboard-tracking`
  - `codex/ws-c-tailor-pdf`
  - `codex/ws-d-audit-compliance`
- Every PR must include:
  - contract compliance checklist
  - tests added/updated
  - explicit non-goals not touched

## Drift Control

If a workstream needs contract changes:

1. Stop coding that part.
2. Propose contract delta in this thread.
3. Update `docs/architecture/BUILD_CONTRACT.md`.
4. Resume implementation only after contract update.

## Definition of Done (Program-Level)

1. All four workstreams merged without contract conflicts.
2. End-to-end flow passes:
   - capture -> application created
   - resume generated -> compliance checked
   - user approval recorded -> status ready_to_apply
3. Compliance rules from `docs/architecture/SAFETY_COMPLIANCE.md` are enforced in code and tests.
