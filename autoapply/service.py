from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass

from autoapply.artifacts import ArtifactWriter
from autoapply.compliance import ComplianceGate
from autoapply.contracts import (
    ApprovalState,
    ChangeLog,
    ClaimMapEntry,
    GenerateResumeRequest,
    GenerateResumeResult,
    JobPosting,
    RenderModel,
    ResumeVersion,
    UserProfile,
    render_model_to_json_dict,
    utc_now_iso,
)
from autoapply.repositories import GenerateRepository
from autoapply.tailoring import TailoringEngine


@dataclass(frozen=True)
class GenerationOutcome:
    status_code: int
    result: GenerateResumeResult


class ResumeGenerationService:
    def __init__(
        self,
        repository: GenerateRepository,
        tailoring_engine: TailoringEngine,
        artifact_writer: ArtifactWriter,
        compliance_gate: ComplianceGate,
    ) -> None:
        self._repository = repository
        self._tailoring_engine = tailoring_engine
        self._artifact_writer = artifact_writer
        self._compliance_gate = compliance_gate

    def generate_resume_version(
        self,
        application_id: str,
        request: GenerateResumeRequest,
    ) -> GenerationOutcome:
        application = self._repository.get_application(application_id)
        job_posting = self._repository.get_job_posting_for_application(application_id)
        profile = self._repository.get_user_profile()

        render_model = self._tailoring_engine.build_render_model(profile, job_posting)
        claims_map = self._build_claims_map(render_model)

        compliance = self._compliance_gate.validate(profile=profile, claims_map=claims_map)
        if not compliance.ok:
            return GenerationOutcome(
                status_code=422,
                result=GenerateResumeResult(
                    resume_version_id="",
                    warnings=[],
                    blocked_reasons=compliance.blocked_reasons,
                ),
            )

        version_id = self._new_version_id(
            application_id=application.id,
            template_id=request.template_id,
            render_model=render_model,
            current_count=len(self._repository.get_resume_versions_for_application(application_id)),
        )

        html_path, pdf_path = self._artifact_writer.write_resume_artifacts(
            application_id=application.id,
            resume_version_id=version_id,
            render_model=render_model,
        )

        resume_version = ResumeVersion(
            id=version_id,
            application_id=application.id,
            template_id=request.template_id,
            pdf_path=pdf_path,
            rendered_html_path=html_path,
            render_model_json=render_model,
            change_log=ChangeLog(added=[], removed=[], reworded=[]),
            claims_map=claims_map,
            approval=ApprovalState(approved=False, approved_at=None),
            created_at=utc_now_iso(),
        )

        self._repository.save_resume_version(resume_version)

        warnings = self._build_warnings(profile=profile, job_posting=job_posting)

        return GenerationOutcome(
            status_code=201,
            result=GenerateResumeResult(
                resume_version_id=version_id,
                warnings=warnings,
                blocked_reasons=[],
            ),
        )

    def _new_version_id(
        self,
        application_id: str,
        template_id: str,
        render_model: RenderModel,
        current_count: int,
    ) -> str:
        # Deterministic for same data and version index; avoids random UUIDs.
        payload = {
            "application_id": application_id,
            "template_id": template_id,
            "render_model": render_model_to_json_dict(render_model),
            "version_index": current_count,
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return str(uuid.uuid5(uuid.NAMESPACE_URL, digest))

    def _build_claims_map(self, render_model: RenderModel) -> list[ClaimMapEntry]:
        claims: list[ClaimMapEntry] = []
        section_source_map = (
            ("experience", "experience"),
            ("projects", "project"),
        )
        for section_name, source_type in section_source_map:
            claims.extend(
                self._build_section_claims(
                    render_model=render_model,
                    section_name=section_name,
                    source_type=source_type,
                )
            )

        return claims

    def _build_section_claims(
        self,
        *,
        render_model: RenderModel,
        section_name: str,
        source_type: str,
    ) -> list[ClaimMapEntry]:
        claims: list[ClaimMapEntry] = []
        for section in render_model.sections.get(section_name, []):
            for bullet in section.bullets:
                claims.append(
                    ClaimMapEntry(
                        bullet_id=bullet.id,
                        bullet_text=bullet.text,
                        source_type=source_type,
                        source_id=section.entry_id,
                        evidence_text=bullet.text,
                        verification_status="supported",
                    )
                )
        return claims

    def _build_warnings(self, profile: UserProfile, job_posting: JobPosting) -> list[str]:
        warnings: list[str] = []
        if not profile.summary:
            warnings.append("profile summary is empty")
        if not job_posting.structured_json.keywords:
            warnings.append("job posting contains no explicit keywords")
        return warnings
