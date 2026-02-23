STATUS: DONE

branch: `codex/s4-ingestion-backend`  
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s4_a_ingestion_backend`  
commit hash: `0e1ae53`

## Scope Delivered (S4-A)

- Added resume ingestion parser pipeline for `.pdf` and `.docx`.
- Added backend endpoint: `POST /api/v1/profile/resume-parse`.
- Added upload validation and parse failure semantics (`400`, `415`, `422`).
- Added mapping + validation test coverage for parser and API multipart behavior.

## Parsed Output Contract (Explicit)

Endpoint: `POST /api/v1/profile/resume-parse`  
Request: `multipart/form-data`

- `file` (required): uploaded resume file (`.pdf` or `.docx`)
- `profile_id` (optional): non-empty string, defaults to `primary`

Success response (`200`):

```json
{
  "contract_version": "resume_parse.v1",
  "source": {
    "filename": "resume.docx",
    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_type": "docx",
    "size_bytes": 12345
  },
  "profile": {
    "id": "primary",
    "full_name": "Taylor Dev",
    "headline": "Backend Engineer",
    "summary": "Builds reliable backend systems.",
    "experiences": [
      {
        "id": "exp-1",
        "company": "Acme Corp",
        "title": "Senior Backend Engineer",
        "start_date": "2020-01-01",
        "end_date": null,
        "bullets": ["Built Python APIs for ingestion."],
        "skills": ["Python", "SQL"]
      }
    ],
    "projects": [
      {
        "id": "proj-1",
        "name": "AutoApply",
        "description": "Resume tailoring tool",
        "bullets": ["Built FastAPI backend and React UI."],
        "skills": ["FastAPI", "React"],
        "url": "https://github.com/taylor/autoapply"
      }
    ],
    "skills": ["Python", "FastAPI", "SQL", "AWS"],
    "education": [
      {
        "id": "edu-1",
        "school": "RIT",
        "degree": "BS Computer Science",
        "field": null,
        "start_date": "2015-09-01",
        "end_date": "2019-05-01"
      }
    ]
  },
  "warnings": [
    "projects section was empty or not detected"
  ]
}
```

Validation failure (`422`) response:

```json
{
  "detail": "parsed profile failed validation",
  "errors": [
    {
      "field": "profile.full_name",
      "message": "is required"
    }
  ]
}
```

## Tests / Checks Run

- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`
  - Result: `Ran 35 tests in ~15.3s`
  - Result: `OK`

## Assumptions / Risks

- Assumption: S4-B will call `POST /api/v1/profile/resume-parse` via multipart and handle returned `profile` draft before writing `/api/v1/profile`.
- Assumption: `resume_parse.v1` is the agreed S4 contract baseline for ingestion.
- Risk: PDF text extraction is intentionally lightweight (`( ... ) Tj/TJ` token extraction) and may miss complex/compressed PDFs.
- Risk: Heuristic mapping can misclassify sections on uncommon resume formats.
- Risk: Date parsing currently supports common `YYYY` and `Mon YYYY` patterns, not all locale/format variants.

## What Worked

- Multipart upload handling integrated cleanly with existing HTTP server design.
- Contracted parse response made test assertions straightforward.
- Unit + API tests catch both mapping quality and request-validation regressions.

## What Broke

- Parallel `git add`/`git commit` attempt caused an `index.lock` race (resolved by retrying sequentially).
- Writing new sprint directories in this worktree required elevated sandbox permission.

## Improve Next Sprint

- Expand PDF extraction robustness (compressed streams, wider operator coverage).
- Add richer normalization for experience/project parsing and broader date formats.
- Add fixture corpus for real-world resume layout variants and precision/recall measurement.
