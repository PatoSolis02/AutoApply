# Packaging and Release Runbook

Last updated: 2026-02-25  
Owner: Sprint 08 Thread C (`AUT-19`)

## Purpose

This is the canonical packaging/release runbook for AutoApply.
It standardizes backend, frontend, and extension artifact preparation in one repeatable flow.

Use this runbook for release preparation. Do not use historical sprint handoffs/reflections as release instructions.

## Scope and Assumptions

- Scope: packaging + release validation documentation only (no runtime behavior changes).
- Repository workflow baseline: branch from `codex/integration`, one worktree per active thread.
- All commands below run from repository root unless noted.

## 0) Initialize Release Variables

```bash
export RELEASE_TAG="$(date +%Y%m%d)-$(git rev-parse --short HEAD)"
export RELEASE_DIR="dist/release/${RELEASE_TAG}"
mkdir -p "${RELEASE_DIR}"
```

## 1) Preflight Guardrails (Required)

```bash
python3 scripts/check_runtime_versions.py
python3 scripts/check_tracked_artifacts.py
```

## 2) Version Alignment Check (Required)

Ensure backend/frontend/extension versions match before packaging.

```bash
python3 - <<'PY'
import json
import tomllib
from pathlib import Path

root = Path(".")
versions = {
    "frontend": json.loads((root / "package.json").read_text(encoding="utf-8"))["version"],
    "backend": tomllib.loads((root / "backend/pyproject.toml").read_text(encoding="utf-8"))["project"]["version"],
    "extension": json.loads((root / "extension/manifest.json").read_text(encoding="utf-8"))["version"],
}
for name, value in versions.items():
    print(f"{name}: {value}")
if len(set(versions.values())) != 1:
    raise SystemExit("Version mismatch detected across frontend/backend/extension.")
PY
```

## 3) Validation Gates (CI Parity, Required)

Run the same checks used by `.github/workflows/ci.yml`:

```bash
npm ci
npm test
npm run build
PYTHONPATH=. python3 -m unittest tests.test_tailoring tests.test_generation_pipeline tests.test_generation_api
PYTHONPATH=src python3 -m unittest tests.test_ws_d_audit_compliance
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_workflow_smoke_api.py'
```

## 4) Package Frontend Artifact

```bash
tar -czf "${RELEASE_DIR}/frontend-${RELEASE_TAG}.tar.gz" \
  dist \
  index.html \
  package.json \
  package-lock.json
```

## 5) Package Backend Artifact

```bash
tar -czf "${RELEASE_DIR}/backend-${RELEASE_TAG}.tar.gz" \
  backend \
  autoapply \
  scripts \
  .python-version \
  .nvmrc
```

## 6) Package Extension Artifact

```bash
(
  cd extension
  zip -r "../${RELEASE_DIR}/extension-${RELEASE_TAG}.zip" \
    manifest.json \
    popup.html \
    popup.js \
    content.js
)
```

## 7) Emit Checksums and Release Metadata

```bash
python3 - <<'PY'
import hashlib
import os
from pathlib import Path

release_dir = Path(os.environ["RELEASE_DIR"])
artifacts = sorted(path for path in release_dir.iterdir() if path.is_file())
checksum_lines = []
for path in artifacts:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_lines.append(f"{digest}  {path.name}")
(release_dir / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
print(f"Wrote {release_dir / 'SHA256SUMS.txt'}")
PY

{
  echo "release_tag=${RELEASE_TAG}"
  echo "commit=$(git rev-parse HEAD)"
  echo "branch=$(git rev-parse --abbrev-ref HEAD)"
  echo "generated_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${RELEASE_DIR}/release-metadata.txt"

ls -lh "${RELEASE_DIR}"
```

## 8) Rollback Guidance

- If any validation gate fails, stop release packaging and fix failures before retrying.
- If artifacts were already distributed, revert to the previous known-good release tag/artifacts and rerun validation before re-publishing.
- Keep release metadata and checksums for traceability in handoff/integration records.
