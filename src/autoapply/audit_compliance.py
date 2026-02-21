"""WS-D audit/compliance module for resume version generation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import re
from typing import Dict, Literal, Optional
from uuid import uuid4

SourceType = Literal["experience", "project", "education", "skill"]
RewordReason = Literal["job_alignment", "clarity", "brevity"]

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


class ContractError(Exception):
    """Contract-aware error used to emulate API status behavior."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class ComplianceError(ContractError):
    """Raised when compliance gates fail."""

    def __init__(self, message: str) -> None:
        super().__init__(422, message)


class ConflictError(ContractError):
    """Raised when a state transition is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(409, message)


class NotFoundError(ContractError):
    """Raised when a required entity cannot be found."""

    def __init__(self, message: str) -> None:
        super().__init__(404, message)


@dataclass(frozen=True)
class ProfileItem:
    id: str
    text: str


@dataclass(frozen=True)
class DraftBullet:
    bullet_id: str
    bullet_text: str
    source_type: SourceType
    source_id: str
    reword_reason: RewordReason = "clarity"


@dataclass(frozen=True)
class ResumeDraft:
    application_id: str
    template_id: str
    headline: str
    summary: str
    selected_bullets: tuple[DraftBullet, ...]


@dataclass(frozen=True)
class RewordedChange:
    from_text: str
    to_text: str
    reason: RewordReason


@dataclass(frozen=True)
class ChangeLog:
    added: tuple[str, ...]
    removed: tuple[str, ...]
    reworded: tuple[RewordedChange, ...]


@dataclass(frozen=True)
class ClaimEvidence:
    bullet_id: str
    bullet_text: str
    source_type: SourceType
    source_id: str
    evidence_text: str
    verification_status: Literal["supported", "rejected"]


@dataclass(frozen=True)
class ApprovalState:
    approved: bool
    approved_at: Optional[str]


@dataclass(frozen=True)
class ResumeVersion:
    id: str
    application_id: str
    template_id: str
    pdf_path: str
    rendered_html_path: str
    render_model_json: dict
    change_log: ChangeLog
    claims_map: tuple[ClaimEvidence, ...]
    approval: ApprovalState
    created_at: str


@dataclass
class ApplicationRecord:
    id: str
    status: str = "drafting"
    latest_resume_version_id: Optional[str] = None


@dataclass(frozen=True)
class UserProfile:
    full_name: str
    headline: Optional[str]
    summary: Optional[str]
    experiences: tuple[ProfileItem, ...] = field(default_factory=tuple)
    projects: tuple[ProfileItem, ...] = field(default_factory=tuple)
    skills: tuple[ProfileItem, ...] = field(default_factory=tuple)
    education: tuple[ProfileItem, ...] = field(default_factory=tuple)

    def source_index(self) -> Dict[tuple[SourceType, str], str]:
        index: Dict[tuple[SourceType, str], str] = {}
        for item in self.experiences:
            index[("experience", item.id)] = item.text
        for item in self.projects:
            index[("project", item.id)] = item.text
        for item in self.education:
            index[("education", item.id)] = item.text
        for item in self.skills:
            index[("skill", item.id)] = item.text
        return index


class InMemoryStore:
    """Persistence adapter used for deterministic WS-D tests."""

    def __init__(self) -> None:
        self.applications: dict[str, ApplicationRecord] = {}
        self.resume_versions: dict[str, ResumeVersion] = {}
        self.resume_versions_by_application: dict[str, list[str]] = {}

    def create_application(self, application_id: str, status: str = "drafting") -> ApplicationRecord:
        record = ApplicationRecord(id=application_id, status=status)
        self.applications[application_id] = record
        self.resume_versions_by_application.setdefault(application_id, [])
        return deepcopy(record)

    def get_application(self, application_id: str) -> ApplicationRecord:
        if application_id not in self.applications:
            raise NotFoundError(f"application '{application_id}' not found")
        return deepcopy(self.applications[application_id])

    def get_latest_resume_version(self, application_id: str) -> Optional[ResumeVersion]:
        ids = self.resume_versions_by_application.get(application_id, [])
        if not ids:
            return None
        return deepcopy(self.resume_versions[ids[-1]])

    def _persist_resume_version(self, version: ResumeVersion) -> ResumeVersion:
        if version.application_id not in self.applications:
            raise NotFoundError(f"application '{version.application_id}' not found")
        self.resume_versions[version.id] = version
        self.resume_versions_by_application.setdefault(version.application_id, []).append(version.id)
        self.applications[version.application_id].latest_resume_version_id = version.id
        return deepcopy(version)

    def get_resume_version(self, resume_version_id: str) -> ResumeVersion:
        if resume_version_id not in self.resume_versions:
            raise NotFoundError(f"resume_version '{resume_version_id}' not found")
        return deepcopy(self.resume_versions[resume_version_id])

    def approve_resume_version(self, resume_version_id: str) -> ResumeVersion:
        current = self.get_resume_version(resume_version_id)
        approved = replace(
            current,
            approval=ApprovalState(approved=True, approved_at=_utc_now_iso()),
        )
        self.resume_versions[resume_version_id] = approved
        return deepcopy(approved)

    def set_application_status(self, application_id: str, target_status: str) -> ApplicationRecord:
        app = self.get_application(application_id)
        _validate_status_transition(app.status, target_status)
        if target_status == "ready_to_apply":
            latest = self.get_latest_resume_version(application_id)
            if latest is None or not latest.approval.approved:
                raise ComplianceError(
                    "approval gate failed: latest resume version must be approved before ready_to_apply"
                )
        self.applications[application_id].status = target_status
        return deepcopy(self.applications[application_id])


class AuditComplianceEngine:
    """Generates and validates change log + claims map before persistence."""

    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def generate_resume_version(self, profile: UserProfile, draft: ResumeDraft) -> ResumeVersion:
        self._validate_profile(profile)
        self.store.get_application(draft.application_id)

        source_index = profile.source_index()
        claims_map = self._generate_claims_map(draft, source_index)
        if any(claim.verification_status == "rejected" for claim in claims_map):
            raise ComplianceError("unsupported claims detected in draft bullets")

        previous = self.store.get_latest_resume_version(draft.application_id)
        change_log = self._generate_change_log(previous, draft)

        version_id = str(uuid4())
        root = f"artifacts/resumes/{draft.application_id}"
        render_model_json = {
            "headline": draft.headline,
            "summary": draft.summary,
            "sections": {
                "bullets": [
                    {
                        "id": bullet.bullet_id,
                        "text": bullet.bullet_text,
                        "source_type": bullet.source_type,
                        "source_id": bullet.source_id,
                    }
                    for bullet in draft.selected_bullets
                ]
            },
        }
        version = ResumeVersion(
            id=version_id,
            application_id=draft.application_id,
            template_id=draft.template_id,
            pdf_path=f"{root}/{version_id}.pdf",
            rendered_html_path=f"{root}/{version_id}.html",
            render_model_json=render_model_json,
            change_log=change_log,
            claims_map=claims_map,
            approval=ApprovalState(approved=False, approved_at=None),
            created_at=_utc_now_iso(),
        )
        return self.store._persist_resume_version(version)

    def approve_resume_version(self, resume_version_id: str) -> ResumeVersion:
        return self.store.approve_resume_version(resume_version_id)

    def set_application_status(self, application_id: str, target_status: str) -> ApplicationRecord:
        return self.store.set_application_status(application_id, target_status)

    def _validate_profile(self, profile: UserProfile) -> None:
        if not profile.full_name.strip():
            raise ComplianceError("profile missing required identity field: full_name")
        if not profile.source_index():
            raise ComplianceError("profile is empty; at least one source item is required")

    def _generate_claims_map(
        self,
        draft: ResumeDraft,
        source_index: dict[tuple[SourceType, str], str],
    ) -> tuple[ClaimEvidence, ...]:
        claims: list[ClaimEvidence] = []
        for bullet in draft.selected_bullets:
            key = (bullet.source_type, bullet.source_id)
            evidence = source_index.get(key, "")
            if not evidence:
                claims.append(
                    ClaimEvidence(
                        bullet_id=bullet.bullet_id,
                        bullet_text=bullet.bullet_text,
                        source_type=bullet.source_type,
                        source_id=bullet.source_id,
                        evidence_text="",
                        verification_status="rejected",
                    )
                )
                continue
            supported = _is_supported_claim(bullet.bullet_text, evidence)
            claims.append(
                ClaimEvidence(
                    bullet_id=bullet.bullet_id,
                    bullet_text=bullet.bullet_text,
                    source_type=bullet.source_type,
                    source_id=bullet.source_id,
                    evidence_text=evidence,
                    verification_status="supported" if supported else "rejected",
                )
            )
        return tuple(claims)

    def _generate_change_log(self, previous: Optional[ResumeVersion], draft: ResumeDraft) -> ChangeLog:
        current_by_id = {bullet.bullet_id: bullet for bullet in draft.selected_bullets}
        if previous is None:
            return ChangeLog(
                added=tuple(bullet.bullet_text for bullet in draft.selected_bullets),
                removed=tuple(),
                reworded=tuple(),
            )

        previous_by_id = {
            bullet["id"]: bullet["text"]
            for bullet in previous.render_model_json.get("sections", {}).get("bullets", [])
        }

        added_ids = sorted(set(current_by_id) - set(previous_by_id))
        removed_ids = sorted(set(previous_by_id) - set(current_by_id))
        shared_ids = sorted(set(current_by_id) & set(previous_by_id))

        added = tuple(current_by_id[bullet_id].bullet_text for bullet_id in added_ids)
        removed = tuple(previous_by_id[bullet_id] for bullet_id in removed_ids)
        reworded = tuple(
            RewordedChange(
                from_text=previous_by_id[bullet_id],
                to_text=current_by_id[bullet_id].bullet_text,
                reason=current_by_id[bullet_id].reword_reason,
            )
            for bullet_id in shared_ids
            if previous_by_id[bullet_id] != current_by_id[bullet_id].bullet_text
        )

        return ChangeLog(added=added, removed=removed, reworded=reworded)


def _normalize_tokens(text: str) -> set[str]:
    tokens = {token for token in _TOKEN_PATTERN.findall(text.lower())}
    return {token for token in tokens if token not in _STOPWORDS}


def _is_supported_claim(bullet_text: str, evidence_text: str) -> bool:
    bullet_tokens = _normalize_tokens(bullet_text)
    evidence_tokens = _normalize_tokens(evidence_text)
    if not bullet_tokens or not evidence_tokens:
        return False
    return bullet_tokens.issubset(evidence_tokens)


def _validate_status_transition(current: str, target: str) -> None:
    allowed = {
        "captured": {"drafting", "rejected"},
        "drafting": {"ready_to_apply", "captured", "rejected"},
        "ready_to_apply": {"applied", "drafting", "rejected"},
        "applied": {"interview", "offer", "rejected"},
        "interview": {"offer", "rejected"},
        "offer": set(),
        "rejected": set(),
    }
    if current not in allowed:
        raise ConflictError(f"unknown current status '{current}'")
    if target not in allowed[current]:
        raise ConflictError(f"invalid transition '{current}' -> '{target}'")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
