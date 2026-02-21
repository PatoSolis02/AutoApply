from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
from uuid import uuid4


class CaptureDatabase:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        migration_dir = Path(__file__).resolve().parent.parent / "migrations"
        migration_paths = sorted(migration_dir.glob("*.sql"))
        with self.connect() as conn:
            for path in migration_paths:
                conn.executescript(path.read_text(encoding="utf-8"))
            conn.commit()

    def insert_capture(
        self,
        *,
        title: str,
        company: str,
        location: Optional[str],
        job_url: str,
        description_raw: str,
        captured_at: str,
        structured_json: Dict[str, object],
    ) -> Tuple[str, str]:
        now = datetime.now(timezone.utc).isoformat()
        application_id = str(uuid4())
        job_posting_id = str(uuid4())

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO applications (
                    id, company, role_title, job_url, job_source, location,
                    status, notes, fit_score, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    application_id,
                    company,
                    title,
                    job_url,
                    "linkedin",
                    location,
                    "captured",
                    "",
                    None,
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO job_postings (
                    id, application_id, raw_text, structured_json, captured_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job_posting_id,
                    application_id,
                    description_raw,
                    json.dumps(structured_json),
                    captured_at,
                ),
            )
            conn.commit()

        return application_id, job_posting_id

    def list_applications(
        self,
        *,
        status: Optional[str],
        company: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, object]], int]:
        conditions: list[str] = []
        params: list[object] = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if company:
            conditions.append("LOWER(company) LIKE LOWER(?)")
            params.append(f"%{company}%")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (page - 1) * page_size

        with self.connect() as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) AS total FROM applications {where_clause}",
                tuple(params),
            ).fetchone()
            rows = conn.execute(
                f"""
                SELECT
                    id, company, role_title, job_url, job_source, location,
                    status, notes, fit_score, created_at, updated_at
                FROM applications
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [page_size, offset]),
            ).fetchall()

        total = int(total_row["total"]) if total_row else 0
        return [self._row_to_application(row) for row in rows], total

    def get_application(self, application_id: str) -> Optional[dict[str, object]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id, company, role_title, job_url, job_source, location,
                    status, notes, fit_score, created_at, updated_at
                FROM applications
                WHERE id = ?
                """,
                (application_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_application(row)

    def update_application_status(
        self,
        application_id: str,
        target_status: str,
        *,
        updated_at: str,
    ) -> Optional[dict[str, object]]:
        with self.connect() as conn:
            result = conn.execute(
                """
                UPDATE applications
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (target_status, updated_at, application_id),
            )
            if result.rowcount == 0:
                return None
            conn.commit()

        return self.get_application(application_id)

    def list_resume_versions(self, application_id: str) -> list[dict[str, object]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id, application_id, template_id, pdf_path, rendered_html_path,
                    approval_approved, approval_approved_at, created_at
                FROM resume_versions
                WHERE application_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (application_id,),
            ).fetchall()
        return [self._row_to_resume_timeline(row) for row in rows]

    def get_latest_resume_version(self, application_id: str) -> Optional[dict[str, object]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id, application_id, template_id, pdf_path, rendered_html_path,
                    approval_approved, approval_approved_at, created_at
                FROM resume_versions
                WHERE application_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (application_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_resume_timeline(row)

    def get_resume_version(self, resume_version_id: str) -> Optional[dict[str, object]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id, application_id, template_id, pdf_path, rendered_html_path,
                    render_model_json, change_log, claims_map,
                    approval_approved, approval_approved_at, created_at
                FROM resume_versions
                WHERE id = ?
                """,
                (resume_version_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_resume_detail(row)

    def approve_resume_version(self, resume_version_id: str, *, approved_at: str) -> Optional[dict[str, object]]:
        current = self.get_resume_version(resume_version_id)
        if current is None:
            return None
        approval = current.get("approval", {})
        if isinstance(approval, dict) and approval.get("approved") is True:
            return current

        with self.connect() as conn:
            conn.execute(
                """
                UPDATE resume_versions
                SET approval_approved = 1, approval_approved_at = ?
                WHERE id = ?
                """,
                (approved_at, resume_version_id),
            )
            conn.commit()

        return self.get_resume_version(resume_version_id)

    def insert_resume_version(
        self,
        *,
        application_id: str,
        template_id: str,
        render_model_json: Dict[str, Any],
        change_log: Dict[str, Any],
        claims_map: list[Dict[str, Any]],
        approval_approved: bool = False,
        approval_approved_at: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> str:
        resume_version_id = str(uuid4())
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        root = f"artifacts/resumes/{application_id}"
        pdf_path = f"{root}/{resume_version_id}.pdf"
        html_path = f"{root}/{resume_version_id}.html"

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO resume_versions (
                    id, application_id, template_id, pdf_path, rendered_html_path,
                    render_model_json, change_log, claims_map,
                    approval_approved, approval_approved_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resume_version_id,
                    application_id,
                    template_id,
                    pdf_path,
                    html_path,
                    json.dumps(render_model_json),
                    json.dumps(change_log),
                    json.dumps(claims_map),
                    1 if approval_approved else 0,
                    approval_approved_at,
                    timestamp,
                ),
            )
            conn.commit()

        return resume_version_id

    def _row_to_application(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": row["id"],
            "company": row["company"],
            "role_title": row["role_title"],
            "job_url": row["job_url"],
            "job_source": row["job_source"],
            "location": row["location"],
            "status": row["status"],
            "notes": row["notes"],
            "fit_score": row["fit_score"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _row_to_resume_timeline(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": row["id"],
            "application_id": row["application_id"],
            "template_id": row["template_id"],
            "pdf_path": row["pdf_path"],
            "rendered_html_path": row["rendered_html_path"],
            "approval": {
                "approved": bool(row["approval_approved"]),
                "approved_at": row["approval_approved_at"],
            },
            "created_at": row["created_at"],
        }

    def _row_to_resume_detail(self, row: sqlite3.Row) -> dict[str, object]:
        timeline = self._row_to_resume_timeline(row)
        return {
            **timeline,
            "render_model_json": self._parse_json_object(row["render_model_json"]),
            "change_log": self._parse_json_object(row["change_log"]),
            "claims_map": self._parse_json_list(row["claims_map"]),
        }

    def _parse_json_object(self, value: object) -> dict[str, Any]:
        if not isinstance(value, str):
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _parse_json_list(self, value: object) -> list[dict[str, Any]]:
        if not isinstance(value, str):
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [item for item in parsed if isinstance(item, dict)]
