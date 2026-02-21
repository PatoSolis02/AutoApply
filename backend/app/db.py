from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
from uuid import uuid4


class DbError(Exception):
    """Base db runtime error."""


class DbNotFoundError(DbError):
    """Raised when a required row is missing."""


class DbConflictError(DbError):
    """Raised for contract invalid transitions."""


class DbComplianceError(DbError):
    """Raised for compliance/approval gate failures."""


_ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "captured": {"drafting", "rejected"},
    "drafting": {"ready_to_apply", "captured", "rejected"},
    "ready_to_apply": {"applied", "drafting", "rejected"},
    "applied": {"interview", "offer", "rejected"},
    "interview": {"offer", "rejected"},
    "offer": set(),
    "rejected": set(),
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        now = _utc_now_iso()
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

    def get_application(self, application_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, company, role_title, job_url, job_source, location,
                       status, notes, fit_score, created_at, updated_at
                FROM applications
                WHERE id = ?
                """,
                (application_id,),
            ).fetchone()
        if row is None:
            raise DbNotFoundError(f"application '{application_id}' not found")
        return self._row_to_application(row)

    def get_job_posting_for_application(self, application_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, application_id, raw_text, structured_json, captured_at
                FROM job_postings
                WHERE application_id = ?
                ORDER BY captured_at DESC, id DESC
                LIMIT 1
                """,
                (application_id,),
            ).fetchone()
        if row is None:
            raise DbNotFoundError(f"job posting for application '{application_id}' not found")
        out = dict(row)
        out["structured_json"] = self._parse_json_object(out["structured_json"])
        return out

    def upsert_user_profile(
        self,
        *,
        profile_id: str,
        full_name: str,
        headline: Optional[str],
        summary: Optional[str],
        experiences: list[dict[str, Any]],
        projects: list[dict[str, Any]],
        skills: list[str],
        education: list[dict[str, Any]],
        updated_at: Optional[str] = None,
    ) -> None:
        profile_updated_at = updated_at or _utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO user_profiles (
                    id, full_name, headline, summary, experiences_json, projects_json,
                    skills_json, education_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    full_name = excluded.full_name,
                    headline = excluded.headline,
                    summary = excluded.summary,
                    experiences_json = excluded.experiences_json,
                    projects_json = excluded.projects_json,
                    skills_json = excluded.skills_json,
                    education_json = excluded.education_json,
                    updated_at = excluded.updated_at
                """,
                (
                    profile_id,
                    full_name,
                    headline,
                    summary,
                    json.dumps(experiences),
                    json.dumps(projects),
                    json.dumps(skills),
                    json.dumps(education),
                    profile_updated_at,
                ),
            )
            conn.commit()

    def get_user_profile(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, full_name, headline, summary, experiences_json, projects_json,
                       skills_json, education_json, updated_at
                FROM user_profiles
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            raise DbNotFoundError("user profile not found")

        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "headline": row["headline"],
            "summary": row["summary"],
            "experiences": self._parse_json_list(row["experiences_json"]),
            "projects": self._parse_json_list(row["projects_json"]),
            "skills": [str(skill) for skill in self._parse_json_list(row["skills_json"])],
            "education": self._parse_json_list(row["education_json"]),
            "updated_at": row["updated_at"],
        }

    def list_resume_versions_for_application(self, application_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, application_id, template_id, pdf_path, rendered_html_path,
                       render_model_json, change_log_json, claims_map_json, approval_approved,
                       approval_approved_at, created_at
                FROM resume_versions
                WHERE application_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (application_id,),
            ).fetchall()
        return [self._resume_version_from_row(row) for row in rows]

    def list_resume_versions(self, application_id: str) -> list[dict[str, Any]]:
        return [self._to_resume_timeline(version) for version in self.list_resume_versions_for_application(application_id)]

    def get_latest_resume_version_for_application(self, application_id: str) -> Optional[dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, application_id, template_id, pdf_path, rendered_html_path,
                       render_model_json, change_log_json, claims_map_json, approval_approved,
                       approval_approved_at, created_at
                FROM resume_versions
                WHERE application_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (application_id,),
            ).fetchone()
        if row is None:
            return None
        return self._resume_version_from_row(row)

    def get_latest_resume_version(self, application_id: str) -> Optional[dict[str, Any]]:
        latest = self.get_latest_resume_version_for_application(application_id)
        if latest is None:
            return None
        return self._to_resume_timeline(latest)

    def get_resume_version(self, resume_version_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, application_id, template_id, pdf_path, rendered_html_path,
                       render_model_json, change_log_json, claims_map_json, approval_approved,
                       approval_approved_at, created_at
                FROM resume_versions
                WHERE id = ?
                """,
                (resume_version_id,),
            ).fetchone()
        if row is None:
            raise DbNotFoundError(f"resume_version '{resume_version_id}' not found")
        return self._resume_version_from_row(row)

    def save_resume_version(
        self,
        *,
        id: str,
        application_id: str,
        template_id: str,
        pdf_path: str,
        rendered_html_path: str,
        render_model_json: dict[str, Any],
        change_log_json: dict[str, Any],
        claims_map_json: list[dict[str, Any]],
        approval_approved: bool,
        approval_approved_at: Optional[str],
        created_at: str,
    ) -> None:
        self.get_application(application_id)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO resume_versions (
                    id, application_id, template_id, pdf_path, rendered_html_path,
                    render_model_json, change_log_json, claims_map_json, approval_approved,
                    approval_approved_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id,
                    application_id,
                    template_id,
                    pdf_path,
                    rendered_html_path,
                    json.dumps(render_model_json),
                    json.dumps(change_log_json),
                    json.dumps(claims_map_json),
                    1 if approval_approved else 0,
                    approval_approved_at,
                    created_at,
                ),
            )
            conn.commit()

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
        timestamp = created_at or _utc_now_iso()
        root = f"artifacts/resumes/{application_id}"

        self.save_resume_version(
            id=resume_version_id,
            application_id=application_id,
            template_id=template_id,
            pdf_path=f"{root}/{resume_version_id}.pdf",
            rendered_html_path=f"{root}/{resume_version_id}.html",
            render_model_json=render_model_json,
            change_log_json=change_log,
            claims_map_json=claims_map,
            approval_approved=approval_approved,
            approval_approved_at=approval_approved_at,
            created_at=timestamp,
        )

        return resume_version_id

    def approve_resume_version(self, resume_version_id: str, *, approved_at: Optional[str] = None) -> dict[str, Any]:
        current = self.get_resume_version(resume_version_id)
        if any(item.get("verification_status") == "rejected" for item in current["claims_map"]):
            raise DbComplianceError("unsupported claims detected")

        effective_approved_at = approved_at or current["approval"].get("approved_at") or _utc_now_iso()

        with self.connect() as conn:
            conn.execute(
                """
                UPDATE resume_versions
                SET approval_approved = 1, approval_approved_at = ?
                WHERE id = ?
                """,
                (effective_approved_at, resume_version_id),
            )
            conn.commit()
        return self.get_resume_version(resume_version_id)

    def set_application_status(self, application_id: str, target_status: str) -> dict[str, Any]:
        current = self.get_application(application_id)
        if str(current["status"]) == target_status:
            return current
        self._validate_status_transition(str(current["status"]), target_status)

        if target_status == "ready_to_apply":
            latest = self.get_latest_resume_version_for_application(application_id)
            if latest is None or not bool(latest["approval"].get("approved")):
                raise DbComplianceError(
                    "approval gate failed: latest resume version must be approved before ready_to_apply"
                )

        with self.connect() as conn:
            conn.execute(
                """
                UPDATE applications
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (target_status, _utc_now_iso(), application_id),
            )
            conn.commit()
        return self.get_application(application_id)

    def update_application_status(self, application_id: str, target_status: str, *, updated_at: str) -> dict[str, Any]:
        self.get_application(application_id)
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE applications
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (target_status, updated_at, application_id),
            )
            conn.commit()
        return self.get_application(application_id)

    def _row_to_application(self, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
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

    def _resume_version_from_row(self, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        render_model = self._parse_json_object(row["render_model_json"])
        change_log = self._parse_json_object(row["change_log_json"])
        claims_map = self._parse_json_list(row["claims_map_json"])
        return {
            "id": row["id"],
            "application_id": row["application_id"],
            "template_id": row["template_id"],
            "pdf_path": row["pdf_path"],
            "rendered_html_path": row["rendered_html_path"],
            "render_model_json": render_model,
            "change_log": change_log,
            "claims_map": claims_map,
            "approval": {
                "approved": bool(row["approval_approved"]),
                "approved_at": row["approval_approved_at"],
            },
            "created_at": row["created_at"],
        }

    def _to_resume_timeline(self, resume: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": resume["id"],
            "application_id": resume["application_id"],
            "template_id": resume["template_id"],
            "pdf_path": resume["pdf_path"],
            "rendered_html_path": resume["rendered_html_path"],
            "approval": {
                "approved": bool(resume.get("approval", {}).get("approved", False)),
                "approved_at": resume.get("approval", {}).get("approved_at"),
            },
            "created_at": resume["created_at"],
        }

    def _parse_json_object(self, value: object) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _parse_json_list(self, value: object) -> list[Any]:
        if isinstance(value, list):
            return value
        if not isinstance(value, str):
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []

    def _validate_status_transition(self, current: str, target: str) -> None:
        if current not in _ALLOWED_STATUS_TRANSITIONS:
            raise DbConflictError(f"unknown current status '{current}'")
        if target not in _ALLOWED_STATUS_TRANSITIONS[current]:
            raise DbConflictError(f"invalid transition '{current}' -> '{target}'")
