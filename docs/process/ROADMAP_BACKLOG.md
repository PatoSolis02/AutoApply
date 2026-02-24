# AutoApply Roadmap and Backlog

Last updated: 2026-02-24
Owner: Integration/Product thread

## Current Snapshot

- Sprint 4 integrated on `codex/integration`.
- Core flow works: capture -> generate -> review -> approve -> ready_to_apply.
- Profile UX and resume upload exist end-to-end.
- PDF parsing reliability improved via hotfix (`10cf071`) with compressed stream + ToUnicode support.
- Remaining quality gap: some real resumes still parse imperfectly (content quality, not total failure).

## P0 (Next Sprint) - Stabilize for Wider Testing

1. Resume parsing quality hardening
- Problem: parser succeeds more often, but extracted structure can still be low quality on complex resumes.
- Exit criteria:
  - Add fixture corpus of tricky PDFs/DOCX.
  - Track parse quality metrics (field-level precision/recall proxy).
  - Reduce manual correction rate in profile form.
  - Improve extraction accuracy for personal details, experience/jobs, and skills.

2. Human-friendly UI and navigation
- Problem: current UI works functionally but is not yet optimized for intuitive end-user flow.
- Exit criteria:
  - Streamline primary paths (Profile, Capture, Review, Approve) with clearer navigation labels.
  - Reduce clicks to complete the core workflow.
  - Improve form readability and validation guidance for non-technical users.

3. LinkedIn capture reliability hardening
- Problem: capture intermittently fails depending on LinkedIn page mode/panel state.
- Exit criteria:
  - Expand DOM fallbacks for list/detail variants.
  - Add deterministic extractor fixtures for known layouts.
  - Fewer "missing company/description" capture failures in manual QA.

4. LLM integration for extraction and generation
- Problem: deterministic heuristics alone are not enough for robust resume understanding and high-quality tailoring.
- Exit criteria:
  - Add configurable LLM provider integration for:
    - resume parsing assist (skills, experience, personal info normalization)
    - resume generation/tailoring from job content + user profile
  - Add prompt/version contract docs and deterministic fallback when LLM is unavailable.
  - Add redaction/safety guardrails for sensitive data handling.

5. End-to-end acceptance tests (real workflow)
- Problem: current coverage is strong but mostly unit/integration; browser-level regressions can slip.
- Exit criteria:
  - Add E2E smoke suite for capture -> generate -> approve -> audit export.
  - Include one profile upload flow in the same suite.
  - Add CI gate for this suite (can be nightly if runtime is long).

6. Runtime and API error observability
- Problem: troubleshooting depends on manual local repro.
- Exit criteria:
  - Structured API error logging with correlation IDs.
  - Basic diagnostics panel / health checks for local debugging.
  - "Known failure mode" docs for common setup/runtime issues.

## P1 (Following Sprint) - Product Depth

1. Fit scoring phase execution (`docs/architecture/PHASE_PLAN.md` phase 4)
2. Stronger audit export options for large histories (chunking/streaming/file export mode)
3. Profile authoring quality features (guided edits, consistency checks)
4. Operational docs for packaging/release of extension + app

## Recommended Parallel Split (Do Not Over-Delegate)

1. Thread A: Ingestion and capture reliability
- Backend parser quality + extension extraction robustness.

2. Thread B: Frontend UX and navigation
- Human-friendly navigation, profile correction UX, clearer workflow guidance.

3. Thread C: LLM + QA + observability
- LLM provider wiring/contracts, E2E tests, diagnostics, failure-mode documentation.

Integration thread responsibilities:
- Merge and resolve cross-thread contract conflicts.
- Keep contracts/types stable on `codex/integration`.
- Maintain this file and sprint-level recap artifacts.

## Working Backlog Rules

1. Every delivered thread must update its handoff with:
- commit hash
- tests run
- contract assumptions/risks

2. Sprint close requires:
- `sprints/<sprint>/SPRINT_LOG.md`
- `sprints/<sprint>/RETROSPECTIVE.md`
- per-thread reflections
- roadmap/backlog update in this file

3. Private sample artifacts (resumes, sensitive docs) stay untracked under:
- `artifacts/`
