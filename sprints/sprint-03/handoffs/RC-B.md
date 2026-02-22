STATUS: DONE

branch: codex/rc-b-structure
worktree path: /Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_rc_b_structure
final commit hash: 42c71a7 (structural changeset; handoff metadata committed afterward)

files moved/renamed (with rationale):
- `docs/BUILD_CONTRACT.md` -> `docs/architecture/BUILD_CONTRACT.md` (group architecture contract artifacts under one owner/domain folder).
- `docs/DATA_MODEL.md` -> `docs/architecture/DATA_MODEL.md` (keep canonical data-model specs with architecture docs).
- `docs/IMPLEMENTATION_GUIDANCE.md` -> `docs/architecture/IMPLEMENTATION_GUIDANCE.md` (co-locate implementation guardrails with architecture docs).
- `docs/PHASE_PLAN.md` -> `docs/architecture/PHASE_PLAN.md` (keep roadmap/planning architecture materials together).
- `docs/PRD.md` -> `docs/architecture/PRD.md` (place product/design spec alongside architecture references).
- `docs/SAFETY_COMPLIANCE.md` -> `docs/architecture/SAFETY_COMPLIANCE.md` (keep safety/compliance constraints in architecture domain).
- `docs/SYSTEM_DESIGN.md` -> `docs/architecture/SYSTEM_DESIGN.md` (co-locate core system design with architecture specs).
- `docs/PARALLEL_WORKSTREAMS.md` -> `docs/process/PARALLEL_WORKSTREAMS.md` (group execution/process governance docs separately from architecture).
- `docs/THREAD_KICKOFFS.md` -> `docs/process/THREAD_KICKOFFS.md` (group execution kickoff procedures under process docs).
- `docs/TOOLING_BASELINE.md` -> `docs/process/TOOLING_BASELINE.md` (group operational/tooling process standards under process docs).
- `vite.config.js` removed from tracking (generated output; avoid tracked build artifacts/noise).
- `vite.config.d.ts` removed from tracking (generated output; avoid tracked build artifacts/noise).

related path/doc updates:
- Updated sprint docs and process docs that referenced moved `docs/...` files so navigation and references remain valid.
- Updated `tsconfig.node.json` with `noEmit: true` to prevent regenerating tracked Vite config artifacts.
- Updated `.gitignore` to ignore generated `vite.config.js` and `vite.config.d.ts`.

tests run + results:
- `PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api tests.test_ws_d_audit_compliance`
  - Result: PASS (14/14)
- `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`
  - Result: PASS (17/17)
- `npm test`
  - Result: PASS (3 test files, 6 tests)
- `npm run build`
  - Result: PASS (production bundle builds successfully)
- `PYTHONPATH=backend python3 -c "from app.main import create_server; s=create_server(db_path='/tmp/autoapply_rc_b.db', port=0); print(s.server_address); s.server_close()"`
  - Result: PASS (server instantiated and bound/closed on localhost ephemeral port)

follow-up items that should be sequential (not parallel):
1. Add a root `README.md` navigation index pointing to `docs/architecture/` and `docs/process/` to reduce onboarding friction.
2. Standardize historical sprint document links that still embed absolute machine-specific paths (optional cleanup-only pass).
3. Evaluate whether a dedicated `frontend/` root (for `src/`, Vite config, and package metadata) is worth a separate migration pass after integration freeze.
