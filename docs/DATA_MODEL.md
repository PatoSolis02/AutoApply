# AutoApply --- Data Model (v0)

## Application

Fields: - id (UUID) - company (string) - role_title (string) - job_url
(string) - job_source ("linkedin") - location (optional) - status
(captured, drafting, ready_to_apply, applied, interview, rejected,
offer) - notes (text) - created_at - updated_at

------------------------------------------------------------------------

## JobPosting

Fields: - id (UUID) - application_id (FK) - raw_text (full job
description) - structured_json (parsed sections) - captured_at

------------------------------------------------------------------------

## ResumeVersion

Fields: - id (UUID) - application_id (FK) - template_id - pdf_path -
rendered_html_path - change_log - claims_map (bullet → source profile
item) - created_at

------------------------------------------------------------------------

## UserProfile

Fields: - id (UUID) - base_resume_text or structured JSON -
experiences\[\] - projects\[\] - skills\[\] - education\[\] - updated_at
