# AutoApply - Product Requirements Document (v0.3)

## 1. Vision

AutoApply is a human-in-the-loop job application assistant focused on helping users prepare high-quality, truthful applications faster.

The system enables users to:

- Create an account and log in
- Capture real job postings (LinkedIn-first)
- Ingest a resume and auto-fill a structured profile
- Generate truthful, tailored resumes per job with explicit user control
- Track applications through core status stages

The system never auto-submits applications and never fabricates information.

## 2. Target User

MVP users: individual job seekers applying to Software Engineering roles.

## 3. Core Workflow

1. User creates an account or logs in.
2. User opens a job page and captures it.
3. System stores application and job-posting data.
4. User uploads a resume; system auto-fills profile sections:
- experiences
- projects
- skills
5. User reviews/edits profile and chooses inputs for tailoring:
- selected experiences
- selected projects
- selected skills
- target keywords
6. User generates a tailored resume for the selected job.
7. User reviews output and manually applies externally.
8. User tracks application status in AutoApply.

## 4. MVP Functional Goals

- Account creation, login, and user-session continuity
- Reliable real-job capture with actionable failure messages
- Resume ingest with profile auto-fill and editable profile sections
- Tailored resume generation with user-controlled input selection
- Defined and stable generated-resume format contract
- Application tracking with practical status transitions
- Truth-bound claims and human approval gate preservation

## 5. Non-Goals (MVP)

- No automated job crawling
- No automated form submission
- No CAPTCHA bypassing
- No falsified qualifications
- No autonomous apply behavior
- No advanced ranking/analytics required for first end-to-end usage

## 6. Success Metrics

Technical:

- High capture reliability on real target pages
- Resume ingest reliably auto-fills profile sections (experiences/projects/skills)
- Tailored resumes generate successfully with defined format compliance
- Zero unsupported/fabricated claims in generated content

Outcome:

- User can complete capture -> profile ingest -> generate -> manual apply -> track flow without blockers
- Reduced time-to-apply versus manual baseline
