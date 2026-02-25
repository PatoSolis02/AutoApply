# AutoApply MVP Scope (Source of Truth)

Last updated: 2026-02-25  
Owner: Integration/Product thread

## Product Goal

Ship a usable, human-in-the-loop job-application assistant where a user can:

1. Create an account and log in.
2. Reliably capture a real job posting.
3. Ingest a resume and auto-fill profile sections.
4. Generate a tailored resume for a specific job with explicit user controls.
5. Manually apply using the generated resume.
6. Track application status end-to-end.

## MVP In Scope (Must-Have)

1. Account and login
- user registration/authentication
- persistent user session
- per-user data isolation for profile/applications

2. Job capture reliability
- capture from real job pages (LinkedIn-first)
- required-field extraction reliability with actionable failure messages
- persistence of source job data for downstream generation

3. Resume ingest and profile auto-fill
- upload and parse resume
- auto-fill profile with normalized sections:
  - experiences
  - projects
  - skills
- user can review/edit saved profile data

4. Tailored resume generation
- generate resume for one selected application/job
- user can choose which experiences/projects/skills/keywords to include
- output format is explicitly defined and stable (template/section contract)
- claims remain truth-bound to user-provided/source-backed data

5. Human-in-the-loop apply
- system prepares final resume artifact and metadata
- user manually submits application outside the system
- no autonomous application submission

6. Application tracking
- create/update core statuses for each application
- visible per-application timeline/history sufficient for manual workflow management

## MVP Explicitly Out of Scope

1. Autonomous application submission or browser autofill bot behavior.
2. Advanced scoring/ranking intelligence that is not required for first successful end-to-end usage.
3. Advanced export/reporting features beyond what is required to support tracking and manual review.
4. Non-critical polish/refactors that do not improve the core MVP flow reliability.

## MVP Acceptance Criteria

MVP is complete only when all are true:

1. New user can sign up, sign in, and keep a working session.
2. User can capture at least one real job posting and see it persisted.
3. User can upload a resume and see profile sections auto-filled (experiences/projects/skills), then edit and save.
4. User can generate a tailored resume for that job with selectable inputs (skills/projects/experiences/keywords).
5. Generated resume format is consistent with a documented contract/template.
6. User can move the application through tracking statuses after manual apply.

## Priority Gates for Sprint Selection

1. `MVP-P0`: required to complete the MVP acceptance criteria above.
2. `MVP-P1`: reliability/quality work needed to make MVP consistently usable.
3. `POST-MVP`: valuable but not required for initial release.

Rule:

- No `POST-MVP` thread should run while open `MVP-P0` work exists, unless explicitly approved as a dependency unblocker.
