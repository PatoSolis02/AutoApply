STATUS: DONE

branch: `codex/s5-parser-quality`  
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_a_parser_quality`  
commit hash: `fc6f384`

## Scope Delivered (`Q-1`, `B-1`)

- Improved deterministic resume field extraction quality in `backend/app/resume_ingest.py`:
  - better personal info parsing (`Name:` labels, metadata/location filtering for headline selection)
  - broader experience heading parsing (`title/company` separator variants and split date lines)
  - stronger date parsing (`MM/YYYY`, `to`, month names) without contract changes
  - skills extraction fallback from parsed experience/project evidence when explicit skills section is missing
- Fixed PDF edge cases:
  - added support for text-show operators `'` and `"`
  - added stream filter-aware decoding for `ASCII85Decode`, `ASCIIHexDecode`, and chained filters with `FlateDecode`
  - retained existing fallback stream decode behavior
- Added parser regressions in `backend/tests/test_resume_ingest.py` for:
  - personal-info/header noise handling
  - experience parsing variants + split date lines
  - inferred-skills fallback
  - filtered PDF streams + `'` operator extraction

## Tests / Checks Run

1. `PYTHONPATH=backend python3 -m unittest backend/tests/test_resume_ingest.py`  
   - `Ran 11 tests`  
   - `OK`
2. `PYTHONPATH=backend python3 -m unittest backend/tests/test_resume_upload_api.py`  
   - `Ran 5 tests`  
   - `OK`
3. `PYTHONPATH=backend python3 -m unittest backend/tests/test_resume_ingest.py backend/tests/test_resume_upload_api.py`  
   - `Ran 16 tests`  
   - `OK`

## Contract Notes

- Response semantics for `/api/v1/profile/resume-parse` remain unchanged:
  - `200` success
  - `400` invalid multipart/request payload
  - `415` unsupported media type
  - `422` parse/validation failure
- Output contract remains `resume_parse.v1`.

## Risks / Assumptions

- Parser remains heuristic and may still misclassify highly unconventional section ordering/layout.
- PDF handling now covers additional common filters/operators but is not a full PDF layout engine.
- Skills fallback is keyword-driven and may miss niche technologies not in deterministic keyword set.
