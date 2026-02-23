STATUS: DONE

branch: `codex/s4-ingestion-backend`  
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s4_a_ingestion_backend`  
commit hash: `0e1ae53`

## Tests / Checks Run + Results

- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`
  - `Ran 35 tests`
  - `OK`

## What Worked

- Keeping an explicit `resume_parse.v1` response contract from day one prevented API ambiguity.
- Parsing/mapping logic in a dedicated module (`backend/app/resume_ingest.py`) kept request handler changes focused.
- Combining parser unit tests with API multipart tests provided fast confidence on both mapping correctness and endpoint semantics.

## What Broke

- One tooling mistake: parallelizing `git add` and `git commit` triggered a transient git lock race.
- Worktree write restrictions required an elevated command for creating new sprint artifact directories.
- Heuristic parsing required tight fixture design to keep deterministic mapping assertions.

## Assumptions / Risks

- Assumption: downstream profile UX thread will treat parse output as draft data and let users confirm/edit before final save.
- Assumption: backend-only ingestion endpoint is acceptable in Sprint 4 before frontend wiring lands.
- Risk: lightweight PDF text extraction does not yet cover all valid PDF encodings or stream compression patterns.
- Risk: section/entry heuristics may degrade on resumes with unconventional ordering or missing headings.
- Risk: parser currently optimizes for stable contract output over perfect semantic accuracy.

## What To Improve Next Sprint

- Add parser evaluation fixtures from real anonymized resumes and track mapping quality metrics.
- Implement stronger PDF extraction fallback path (stream decode + library-backed extraction when available).
- Introduce deterministic normalization for job titles/company detection and ambiguous heading resolution.
- Add endpoint docs in architecture/API docs outside handoff to make cross-thread integration easier.
