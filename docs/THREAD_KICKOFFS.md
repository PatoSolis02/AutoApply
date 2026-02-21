# Thread Kickoffs for Parallel Execution

Use each block as the first message in a separate implementation thread.

## WS-A Kickoff: Capture and Ingest

You are implementing WS-A for AutoApply.

Must follow:

- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/BUILD_CONTRACT.md`
- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/SAFETY_COMPLIANCE.md`

Build:

1. Chrome extension capture action for LinkedIn job pages.
2. Backend `POST /api/v1/jobs/capture`.
3. Persistence for `Application` and `JobPosting`.
4. Tests for payload validation and successful capture flow.

Constraints:

- No schema/API changes unless explicitly proposed back to architecture owner.
- No features outside WS-A scope.

Deliver:

- Code changes.
- Test results.
- Short list of assumptions.

## WS-B Kickoff: Dashboard and Tracking UI

You are implementing WS-B for AutoApply.

Must follow:

- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/BUILD_CONTRACT.md`
- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/SAFETY_COMPLIANCE.md`

Build:

1. Application list and detail pages.
2. Status transition UI wired to `PATCH /api/v1/applications/{id}/status`.
3. Resume version timeline/detail views.
4. Approval action wired to `POST /api/v1/resume-versions/{id}/approve`.
5. UX handling for `409` and `422` errors.

Constraints:

- Consume existing contracts as-is.
- Do not alter backend contracts in this thread.

Deliver:

- UI code changes.
- Screen-level behavior summary.
- Test/build output.

## WS-C Kickoff: Tailoring and PDF Pipeline

You are implementing WS-C for AutoApply.

Must follow:

- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/BUILD_CONTRACT.md`
- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/SAFETY_COMPLIANCE.md`

Build:

1. Tailoring logic from `UserProfile + JobPosting`.
2. Render model generation for resume HTML.
3. PDF generation and artifact storage paths per contract.
4. Endpoint `POST /api/v1/applications/{id}/resume-versions/generate`.

Constraints:

- Deterministic outputs for same inputs.
- No fabricated claims.
- No approval-state shortcuts.

Deliver:

- Pipeline code.
- Unit tests for selection logic and artifact generation.
- Any open contract questions.

## WS-D Kickoff: Audit and Compliance

You are implementing WS-D for AutoApply.

Must follow:

- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/BUILD_CONTRACT.md`
- `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/AutoApply/docs/SAFETY_COMPLIANCE.md`

Build:

1. `change_log` generation and persistence.
2. `claims_map` generation and verifier.
3. Compliance gate enforcement returning `422` on unsupported claims.
4. Version immutability and approval gate tests.

Constraints:

- Claims must map to source profile items.
- No bypass path around compliance checks.

Deliver:

- Audit/compliance code.
- Failing and passing test cases that prove enforcement.
- Residual risk notes.
