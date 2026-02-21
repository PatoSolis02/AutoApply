from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ExperienceEntry:
    id: str
    company: str
    title: str
    start_date: str
    end_date: str | None
    bullets: list[str]
    skills: list[str]


@dataclass(frozen=True)
class ProjectEntry:
    id: str
    name: str
    description: str
    bullets: list[str]
    skills: list[str]
    url: str | None


@dataclass(frozen=True)
class EducationEntry:
    id: str
    school: str
    degree: str
    field: str | None
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True)
class UserProfile:
    id: str
    full_name: str
    headline: str | None
    summary: str | None
    experiences: list[ExperienceEntry]
    projects: list[ProjectEntry]
    skills: list[str]
    education: list[EducationEntry]
    updated_at: str


@dataclass(frozen=True)
class JobStructured:
    summary: str | None
    responsibilities: list[str]
    requirements: list[str]
    preferred_qualifications: list[str]
    tech_stack: list[str]
    employment_type: str
    seniority: str
    keywords: list[str]


@dataclass(frozen=True)
class JobPosting:
    id: str
    application_id: str
    raw_text: str
    structured_json: JobStructured
    captured_at: str


@dataclass(frozen=True)
class Application:
    id: str
    company: str
    role_title: str
    job_url: str
    job_source: str
    location: str | None
    status: str
    notes: str
    fit_score: float | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RenderBullet:
    id: str
    text: str


@dataclass(frozen=True)
class RenderSectionEntry:
    entry_id: str
    bullets: list[RenderBullet]


@dataclass(frozen=True)
class RenderModel:
    headline: str
    summary: str
    selected_experience_ids: list[str]
    selected_project_ids: list[str]
    selected_skill_keywords: list[str]
    sections: dict[str, list[RenderSectionEntry]]


@dataclass(frozen=True)
class RewordedEntry:
    from_text: str
    to_text: str
    reason: str


@dataclass(frozen=True)
class ChangeLog:
    added: list[str]
    removed: list[str]
    reworded: list[RewordedEntry]


@dataclass(frozen=True)
class ClaimMapEntry:
    bullet_id: str
    bullet_text: str
    source_type: str
    source_id: str
    evidence_text: str
    verification_status: str


@dataclass(frozen=True)
class ApprovalState:
    approved: bool
    approved_at: str | None


@dataclass(frozen=True)
class ResumeVersion:
    id: str
    application_id: str
    template_id: str
    pdf_path: str
    rendered_html_path: str
    render_model_json: RenderModel
    change_log: ChangeLog
    claims_map: list[ClaimMapEntry]
    approval: ApprovalState
    created_at: str


@dataclass(frozen=True)
class GenerateResumeRequest:
    template_id: str


@dataclass(frozen=True)
class GenerateResumeResult:
    resume_version_id: str
    warnings: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComplianceResult:
    ok: bool
    blocked_reasons: list[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_model_to_json_dict(model: RenderModel) -> dict[str, Any]:
    return {
        "headline": model.headline,
        "summary": model.summary,
        "selected_experience_ids": model.selected_experience_ids,
        "selected_project_ids": model.selected_project_ids,
        "selected_skill_keywords": model.selected_skill_keywords,
        "sections": {
            "experience": [
                {
                    "entry_id": entry.entry_id,
                    "bullets": [{"id": bullet.id, "text": bullet.text} for bullet in entry.bullets],
                }
                for entry in model.sections.get("experience", [])
            ],
            "projects": [
                {
                    "entry_id": entry.entry_id,
                    "bullets": [{"id": bullet.id, "text": bullet.text} for bullet in entry.bullets],
                }
                for entry in model.sections.get("projects", [])
            ],
        },
    }
