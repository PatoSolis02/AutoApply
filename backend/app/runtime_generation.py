from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any, Callable

from .db import CaptureDatabase, DbNotFoundError

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from autoapply.contracts import (  # noqa: E402
    Application,
    ApprovalState,
    ChangeLog,
    ClaimMapEntry,
    EducationEntry,
    ExperienceEntry,
    JobPosting,
    JobStructured,
    ProjectEntry,
    RenderBullet,
    RenderModel,
    RenderSectionEntry,
    RewordedEntry,
    ResumeVersion,
    UserProfile,
)
from autoapply.repositories import GenerateRepository, NotFoundError  # noqa: E402


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


class SqliteGenerateRepository(GenerateRepository):
    def __init__(self, capture_db: CaptureDatabase) -> None:
        self._db = capture_db

    def get_application(self, application_id: str) -> Application:
        row = self._translate_not_found(lambda: self._db.get_application(application_id))
        return Application(**row)

    def get_job_posting_for_application(self, application_id: str) -> JobPosting:
        row = self._translate_not_found(lambda: self._db.get_job_posting_for_application(application_id))
        return JobPosting(
            id=row["id"],
            application_id=row["application_id"],
            raw_text=row["raw_text"],
            structured_json=JobStructured(**row["structured_json"]),
            captured_at=row["captured_at"],
        )

    def get_user_profile(self) -> UserProfile:
        row = self._translate_not_found(self._db.get_user_profile)

        experiences = [
            self._to_experience_entry(item)
            for item in _as_list(row.get("experiences"))
            if isinstance(item, dict)
        ]
        projects = [
            self._to_project_entry(item)
            for item in _as_list(row.get("projects"))
            if isinstance(item, dict)
        ]
        education = [
            self._to_education_entry(item)
            for item in _as_list(row.get("education"))
            if isinstance(item, dict)
        ]
        skills = [str(skill) for skill in _as_list(row.get("skills"))]

        return UserProfile(
            id=row["id"],
            full_name=row["full_name"],
            headline=row.get("headline"),
            summary=row.get("summary"),
            experiences=experiences,
            projects=projects,
            skills=skills,
            education=education,
            updated_at=row["updated_at"],
        )

    def get_resume_versions_for_application(self, application_id: str) -> list[ResumeVersion]:
        rows = self._db.list_resume_versions_for_application(application_id)
        return [self._to_resume_version(row) for row in rows]

    def save_resume_version(self, resume_version: ResumeVersion) -> None:
        self._db.save_resume_version(
            id=resume_version.id,
            application_id=resume_version.application_id,
            template_id=resume_version.template_id,
            pdf_path=resume_version.pdf_path,
            rendered_html_path=resume_version.rendered_html_path,
            render_model_json=asdict(resume_version.render_model_json),
            change_log_json={
                "added": list(resume_version.change_log.added),
                "removed": list(resume_version.change_log.removed),
                "reworded": [
                    {
                        "from": item.from_text,
                        "to": item.to_text,
                        "reason": item.reason,
                    }
                    for item in resume_version.change_log.reworded
                ],
            },
            claims_map_json=[
                {
                    "bullet_id": claim.bullet_id,
                    "bullet_text": claim.bullet_text,
                    "source_type": claim.source_type,
                    "source_id": claim.source_id,
                    "evidence_text": claim.evidence_text,
                    "verification_status": claim.verification_status,
                }
                for claim in resume_version.claims_map
            ],
            approval_approved=resume_version.approval.approved,
            approval_approved_at=resume_version.approval.approved_at,
            created_at=resume_version.created_at,
        )

    def _to_resume_version(self, row: dict[str, Any]) -> ResumeVersion:
        render_model_raw = row["render_model_json"]
        sections_raw = render_model_raw.get("sections", {})
        render_model = RenderModel(
            headline=str(render_model_raw.get("headline", "")),
            summary=str(render_model_raw.get("summary", "")),
            selected_experience_ids=[str(item) for item in _as_list(render_model_raw.get("selected_experience_ids"))],
            selected_project_ids=[str(item) for item in _as_list(render_model_raw.get("selected_project_ids"))],
            selected_skill_keywords=[str(item) for item in _as_list(render_model_raw.get("selected_skill_keywords"))],
            sections={
                "education": self._to_render_sections(sections_raw.get("education")),
                "experience": self._to_render_sections(sections_raw.get("experience")),
                "projects": self._to_render_sections(sections_raw.get("projects")),
            },
        )

        reworded = [
            RewordedEntry(
                from_text=str(item.get("from", "")),
                to_text=str(item.get("to", "")),
                reason=str(item.get("reason", "clarity")),
            )
            for item in _as_list(row["change_log"].get("reworded"))
            if isinstance(item, dict)
        ]
        claims = [
            ClaimMapEntry(
                bullet_id=str(item.get("bullet_id", "")),
                bullet_text=str(item.get("bullet_text", "")),
                source_type=str(item.get("source_type", "")),
                source_id=str(item.get("source_id", "")),
                evidence_text=str(item.get("evidence_text", "")),
                verification_status=str(item.get("verification_status", "rejected")),
            )
            for item in _as_list(row.get("claims_map"))
            if isinstance(item, dict)
        ]
        return ResumeVersion(
            id=row["id"],
            application_id=row["application_id"],
            template_id=row["template_id"],
            pdf_path=row["pdf_path"],
            rendered_html_path=row["rendered_html_path"],
            render_model_json=render_model,
            change_log=ChangeLog(
                added=[str(item) for item in _as_list(row["change_log"].get("added"))],
                removed=[str(item) for item in _as_list(row["change_log"].get("removed"))],
                reworded=reworded,
            ),
            claims_map=claims,
            approval=ApprovalState(
                approved=bool(row["approval"].get("approved", False)),
                approved_at=row["approval"].get("approved_at"),
            ),
            created_at=row["created_at"],
        )

    def _translate_not_found(self, loader: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        try:
            return loader()
        except DbNotFoundError as err:
            raise NotFoundError(str(err)) from err

    def _to_experience_entry(self, item: dict[str, Any]) -> ExperienceEntry:
        return ExperienceEntry(
            id=str(item.get("id", "")),
            company=str(item.get("company", "")),
            title=str(item.get("title", "")),
            start_date=str(item.get("start_date", "")),
            end_date=item.get("end_date"),
            bullets=[str(bullet) for bullet in _as_list(item.get("bullets"))],
            skills=[str(skill) for skill in _as_list(item.get("skills"))],
        )

    def _to_project_entry(self, item: dict[str, Any]) -> ProjectEntry:
        return ProjectEntry(
            id=str(item.get("id", "")),
            name=str(item.get("name", "")),
            description=str(item.get("description", "")),
            bullets=[str(bullet) for bullet in _as_list(item.get("bullets"))],
            skills=[str(skill) for skill in _as_list(item.get("skills"))],
            url=item.get("url"),
        )

    def _to_education_entry(self, item: dict[str, Any]) -> EducationEntry:
        return EducationEntry(
            id=str(item.get("id", "")),
            school=str(item.get("school", "")),
            degree=str(item.get("degree", "")),
            field=item.get("field"),
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
        )

    def _to_render_sections(self, sections: Any) -> list[RenderSectionEntry]:
        return [
            RenderSectionEntry(
                entry_id=str(section.get("entry_id", "")),
                bullets=self._to_render_bullets(section.get("bullets")),
            )
            for section in _as_list(sections)
            if isinstance(section, dict)
        ]

    def _to_render_bullets(self, bullets: Any) -> list[RenderBullet]:
        return [
            RenderBullet(
                id=str(bullet.get("id", "")),
                text=str(bullet.get("text", "")),
            )
            for bullet in _as_list(bullets)
            if isinstance(bullet, dict)
        ]
