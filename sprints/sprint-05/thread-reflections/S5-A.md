STATUS: DONE

branch: `codex/s5-parser-quality`  
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s5_a_parser_quality`  
commit hash: `fc6f384`

## What Worked

- Keeping parser/API contract behavior fixed while widening extraction heuristics allowed quality improvements with low integration risk.
- Targeted regression tests around real failure shapes (`Name:` headers, split date lines, filtered streams) gave fast confidence.
- Implementing filter-aware PDF decode first made text-operator fixes easier to validate.

## What Broke / Friction

- Sandbox-restricted localhost binding blocked API tests until escalated execution was used.
- Generic month token parsing over-matched (`Labs 2017`) on first pass and required narrowing to explicit month names.

## Risks

- Resume parsing quality still depends on deterministic patterns; unconventional resumes can degrade extraction precision.
- Expanded heading heuristics may still produce occasional title/company inversions on ambiguous lines.

## Follow-up Ideas

1. Add anonymized fixture corpus with precision/recall tracking for name/title/company extraction.
2. Externalize deterministic skill vocabulary for easier updates without parser code edits.
3. Document known unsupported PDF patterns alongside sample artifacts for future fallback design.
