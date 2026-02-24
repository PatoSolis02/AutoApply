STATUS: DONE

branch: `codex/hotfix-pdf-resume-parse`  
scope: backend PDF resume parse reliability (`POST /api/v1/profile/resume-parse`)

## Root Cause

The PDF parser only scanned raw payload text for uncompressed literal operators (`(...) Tj` and array `[...] TJ`).  
Real-world resumes in `artifacts/resume_samples/Redacted Resume.pdf` use Flate-compressed content streams with hex glyph text (`<....> Tj`) and ToUnicode CMaps.  
When those streams were not decoded, extraction produced zero chunks and raised:

- `ResumeParseError: unable to extract text from pdf`

## Fix

- Added PDF stream extraction that:
  - finds `stream ... endstream` blocks
  - tries raw + zlib decompressed variants (standard and raw-deflate)
- Added ToUnicode CMap parsing (`beginbfchar` + `beginbfrange`) to map glyph codes to Unicode text.
- Added hex text-show decoding for:
  - `<...> Tj`
  - `[...] TJ` arrays containing literal and hex fragments
- Kept existing API contract and status semantics unchanged (`200/400/415/422`).
- Expanded date-range parsing to accept ASCII hyphen and common unicode dashes used in PDF text output.

## Validation

- Verified endpoint with real sample:
  - `POST /api/v1/profile/resume-parse` against `artifacts/resume_samples/Redacted Resume.pdf`
  - result: `status 200`, `contract resume_parse.v1`, non-empty parsed profile (`full_name=John`, `experiences=1`)
- Added regression test for compressed hex + ToUnicode PDF extraction:
  - `backend/tests/test_resume_ingest.py::test_parse_pdf_decodes_compressed_hex_stream_using_tounicode_map`
- Full backend suite passes after hotfix.

## Risks

- The parser is still heuristic and not a full PDF text-layout engine; extraction quality can vary across complex PDFs.
- Stream handling currently targets common Flate-based PDFs; uncommon filters/encodings may still require future fallback paths.
- ToUnicode maps are merged from available CMap streams; ambiguous multi-font encodings can still reduce semantic fidelity even when extraction succeeds.
