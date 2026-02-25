# AutoApply Build Contract (v1)

## Purpose

This document locks the architecture and integration contracts so parallel implementation can proceed without drift.

## Non-Negotiable Invariants

1. Human-in-the-loop only. No auto-submission.
2. Truth-bound outputs only. No fabricated claims.
3. Every generated resume version is persisted.
4. LinkedIn capture is user-initiated.
5. Local-first MVP (extension + localhost backend + SQLite).
6. Clear module boundaries:
   - Capture/Ingest
   - Application Tracking
   - Tailoring
   - PDF Rendering
   - Audit/Compliance

## Module Ownership and Boundaries

- `capture`: accepts extension payloads and writes `Application` + `JobPosting`.
- `application_tracking`: status lifecycle, notes, list/detail retrieval.
- `tailoring`: transforms profile + job data into resume content candidates.
- `pdf_rendering`: HTML template render + PDF generation + artifact persistence.
- `audit`: change log, claims map validation, approval gate, immutable version history.

No module is allowed to bypass `audit` when creating a `ResumeVersion`.

## LLM Foundation Contract (Additive)

This phase adds configuration and runtime abstraction only.
Current parser and deterministic tailoring/generation flows remain canonical behavior.

Baseline rules:

1. LLM runtime is disabled by default.
2. If LLM runtime is disabled, unconfigured, or provider calls fail, deterministic behavior must run.
3. Compliance and approval gates remain mandatory regardless of generation path.

Prompt and provider version contract details are specified in:
- `docs/architecture/LLM_FOUNDATION_CONTRACT.md`

Generated resume output format and section-order contract details are specified in:
- `docs/architecture/GENERATION_FORMAT_CONTRACT.md`

## Canonical Data Contracts

### Application

```json
{
  "id": "uuid",
  "company": "string",
  "role_title": "string",
  "job_url": "string",
  "job_source": "linkedin",
  "location": "string|null",
  "status": "captured|drafting|ready_to_apply|applied|interview|rejected|offer",
  "notes": "string",
  "fit_score": "number|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

Allowed transitions:

- `captured -> drafting|rejected`
- `drafting -> ready_to_apply|captured|rejected`
- `ready_to_apply -> applied|drafting|rejected`
- `applied -> interview|offer|rejected`
- `interview -> offer|rejected`
- `offer` and `rejected` are terminal

### JobPosting

```json
{
  "id": "uuid",
  "application_id": "uuid",
  "raw_text": "string",
  "structured_json": {
    "summary": "string|null",
    "responsibilities": ["string"],
    "requirements": ["string"],
    "preferred_qualifications": ["string"],
    "tech_stack": ["string"],
    "employment_type": "full_time|part_time|contract|internship|unknown",
    "seniority": "intern|junior|mid|senior|staff|principal|unknown",
    "keywords": ["string"]
  },
  "captured_at": "datetime"
}
```

### UserProfile

```json
{
  "id": "uuid",
  "full_name": "string",
  "headline": "string|null",
  "summary": "string|null",
  "experiences": [
    {
      "id": "uuid",
      "company": "string",
      "title": "string",
      "start_date": "date",
      "end_date": "date|null",
      "bullets": ["string"],
      "skills": ["string"]
    }
  ],
  "projects": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "bullets": ["string"],
      "skills": ["string"],
      "url": "string|null"
    }
  ],
  "skills": ["string"],
  "education": [
    {
      "id": "uuid",
      "school": "string",
      "degree": "string",
      "field": "string|null",
      "start_date": "date|null",
      "end_date": "date|null"
    }
  ],
  "updated_at": "datetime"
}
```

### ResumeVersion

```json
{
  "id": "uuid",
  "application_id": "uuid",
  "template_id": "string",
  "pdf_path": "string",
  "rendered_html_path": "string",
  "render_model_json": {
    "headline": "string",
    "summary": "string",
    "selected_experience_ids": ["uuid"],
    "selected_project_ids": ["uuid"],
    "selected_skill_keywords": ["string"],
    "sections": {
      "experience": [{"entry_id": "uuid", "bullets": [{"id": "string", "text": "string"}]}],
      "projects": [{"entry_id": "uuid", "bullets": [{"id": "string", "text": "string"}]}]
    }
  },
  "change_log": {
    "added": ["string"],
    "removed": ["string"],
    "reworded": [
      {
        "from": "string",
        "to": "string",
        "reason": "job_alignment|clarity|brevity"
      }
    ]
  },
  "claims_map": [
    {
      "bullet_id": "string",
      "bullet_text": "string",
      "source_type": "experience|project|education|skill",
      "source_id": "uuid|string",
      "evidence_text": "string",
      "verification_status": "supported|rejected"
    }
  ],
  "approval": {
    "approved": "boolean",
    "approved_at": "datetime|null"
  },
  "created_at": "datetime"
}
```

Selection semantics for MVP:

1. `selected_experience_ids`, `selected_project_ids`, and `selected_skill_keywords` are model-selected outputs.
2. The generator must consume full saved profile data plus the target job posting as input.
3. Manual user field-by-field selection is not required for MVP generation.
4. Output format must conform to the generation template contract and visually align to:
- `artifacts/resume_samples/Redacted Resume.pdf`

## API Contract (v1)

Base path: `/api/v1`

- `POST /auth/signup`
  - Request: `email`, `password`.
  - Response: `201` with `user`, `session`, `token`.
  - Conflict: `409` with `error.code=email_exists` when email is already registered.
- `POST /auth/login`
  - Request: `email`, `password`.
  - Response: `200` with `user`, `session`, `token`.
  - Failure: `401` with `error.code=invalid_credentials` for unknown email or wrong password.
- `POST /auth/logout`
  - Request: `Authorization: Bearer <token>`.
  - Response: `200` with `ok=true` and revoked session metadata.
- `GET /auth/session`
  - Request: `Authorization: Bearer <token>`.
  - Response: `200` with `authenticated=true`, `user`, and `session`.
  - Expiry contract: once `expires_at <= now`, response is `401` with `error.code=session_expired` and session is revoked.
  - Revoked/missing session token returns `401` with `error.code=invalid_session`.
- `POST /jobs/capture`
  - Request: title, company, location, job_url, description_raw, captured_at.
  - Response: `201` with `application_id`, `job_posting_id`.
- `GET /applications`
  - Query: status, company, page, page_size.
  - Response: paginated application summaries.
- `GET /applications/{application_id}`
  - Response: application detail + latest resume metadata.
- `PATCH /applications/{application_id}/status`
  - Request: target status.
  - Enforces state transition rules.
- `POST /applications/{application_id}/resume-versions/generate`
  - Request: `template_id`.
  - Runtime input contract: server-side generation uses full user profile + target job posting context.
  - Response: `201` with `resume_version_id`, `warnings`, `blocked_reasons`.
  - Hard fail if unsupported claims exist.
- `GET /applications/{application_id}/resume-versions`
  - Response: version timeline.
- `GET /resume-versions/{resume_version_id}`
  - Response: metadata + `change_log` + `claims_map`.
- `POST /resume-versions/{resume_version_id}/approve`
  - Marks version approved and sets application `status=ready_to_apply`.

## Artifact and Path Conventions

- Root: `artifacts/resumes/`
- Per application: `artifacts/resumes/{application_id}/`
- Filenames:
  - `{resume_version_id}.html`
  - `{resume_version_id}.pdf`

Paths are stored as workspace-relative paths in DB.

## Compliance Gates

Generation must fail when any of these are true:

1. `claims_map.verification_status == rejected` exists.
2. Bullet lacks a source mapping.
3. User profile is empty or missing required identity fields.

Approval gate:

- A resume cannot be considered ready until explicit approval is recorded.

## Error Semantics

- `400`: invalid request payload.
- `401`: auth/session failure (`auth_required`, `invalid_authorization_header`, `invalid_credentials`, `invalid_session`, `session_expired`).
- `404`: missing resource.
- `409`: invalid status transition.
- `422`: unsupported claims or compliance gate failure.
- `500`: internal server error.

## Definition of Done for Contract Compliance

1. Endpoints and payloads match this spec.
2. DB schema supports all required fields.
3. Automated tests cover:
   - status transitions
   - claims gate failures
   - version immutability
   - approval behavior
4. Artifact paths conform to contract.
