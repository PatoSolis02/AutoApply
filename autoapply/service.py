from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from typing import Any

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
    RenderBullet,
    RenderSectionEntry,
    RewordedEntry,
    ResumeVersion,
    UserProfile,
    render_model_to_json_dict,
    utc_now_iso,
)
from autoapply.llm import LlmRuntime, PromptMessage, load_llm_config
from autoapply.repositories import GenerateRepository
from autoapply.tailoring import TailoringEngine

_GENERATE_CONTRACT_VERSION = "resume_generate.v1"
_ALLOWED_REWORD_REASONS = {"job_alignment", "clarity", "brevity"}
_MAX_GENERATION_PROMPT_CHARS = 12000


@dataclass(frozen=True)
class GenerationOutcome:
    status_code: int
    result: GenerateResumeResult


@dataclass(frozen=True)
class _GenerationRenderResult:
    render_model: RenderModel
    change_log: ChangeLog


class ResumeGenerationService:
    def __init__(
        self,
        repository: GenerateRepository,
        tailoring_engine: TailoringEngine,
        artifact_writer: ArtifactWriter,
        compliance_gate: ComplianceGate,
        llm_runtime: LlmRuntime | None = None,
    ) -> None:
        self._repository = repository
        self._tailoring_engine = tailoring_engine
        self._artifact_writer = artifact_writer
        self._compliance_gate = compliance_gate
        self._llm_runtime = llm_runtime or LlmRuntime(load_llm_config())

    def generate_resume_version(
        self,
        application_id: str,
        request: GenerateResumeRequest,
    ) -> GenerationOutcome:
        application = self._repository.get_application(application_id)
        job_posting = self._repository.get_job_posting_for_application(application_id)
        profile = self._repository.get_user_profile()

        deterministic_model = self._tailoring_engine.build_render_model(profile, job_posting)
        source_claim_index = self._build_source_claim_index(deterministic_model)
        generation_render = self._build_render_model(profile, job_posting, deterministic_model)
        claims_map = self._build_claims_map(
            generation_render.render_model,
            source_claim_index=source_claim_index,
        )

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
            render_model=generation_render.render_model,
            current_count=len(self._repository.get_resume_versions_for_application(application_id)),
        )

        html_path, pdf_path = self._artifact_writer.write_resume_artifacts(
            application_id=application.id,
            resume_version_id=version_id,
            render_model=generation_render.render_model,
        )

        resume_version = ResumeVersion(
            id=version_id,
            application_id=application.id,
            template_id=request.template_id,
            pdf_path=pdf_path,
            rendered_html_path=html_path,
            render_model_json=generation_render.render_model,
            change_log=generation_render.change_log,
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

    def _build_render_model(
        self,
        profile: UserProfile,
        job_posting: JobPosting,
        deterministic_model: RenderModel,
    ) -> _GenerationRenderResult:
        baseline = _GenerationRenderResult(
            render_model=deterministic_model,
            change_log=ChangeLog(added=[], removed=[], reworded=[]),
        )
        execution = self._llm_runtime.run_with_fallback(
            workflow="resume_generate",
            messages=self._build_generation_messages(
                profile=profile,
                job_posting=job_posting,
                deterministic_model=deterministic_model,
            ),
            llm_transform=lambda response: self._llm_transform_render_model(
                response_text=response.text,
                baseline=deterministic_model,
            ),
            deterministic_fn=lambda: baseline,
        )
        return execution.value

    def _build_generation_messages(
        self,
        *,
        profile: UserProfile,
        job_posting: JobPosting,
        deterministic_model: RenderModel,
    ) -> list[PromptMessage]:
        profile_json = json.dumps(asdict(profile), ensure_ascii=True)
        job_json = json.dumps(asdict(job_posting), ensure_ascii=True)
        model_json = json.dumps(render_model_to_json_dict(deterministic_model), ensure_ascii=True)
        profile_json = self._truncate_prompt_text(profile_json)
        job_json = self._truncate_prompt_text(job_json)
        model_json = self._truncate_prompt_text(model_json)
        return [
            PromptMessage(
                role="system",
                content=(
                    "You tailor a resume render model for job alignment. "
                    "Do not invent facts. Reword only existing bullet text and keep all bullet IDs unchanged. "
                    "Return JSON only."
                ),
            ),
            PromptMessage(
                role="user",
                content=(
                    f"Contract version: {_GENERATE_CONTRACT_VERSION}\n"
                    "User profile JSON:\n"
                    f"{profile_json}\n\n"
                    "Job posting JSON:\n"
                    f"{job_json}\n\n"
                    "Deterministic render model JSON:\n"
                    f"{model_json}\n\n"
                    "Return JSON using this shape:\n"
                    "{\"reworded\": [{\"bullet_id\": \"<id>\", \"text\": \"<updated bullet>\", "
                    "\"reason\": \"job_alignment|clarity|brevity\"}]}\n"
                    "If no changes are needed, return {\"reworded\": []}."
                ),
            ),
        ]

    def _truncate_prompt_text(self, value: str) -> str:
        if len(value) <= _MAX_GENERATION_PROMPT_CHARS:
            return value
        return value[:_MAX_GENERATION_PROMPT_CHARS]

    def _llm_transform_render_model(
        self,
        *,
        response_text: str,
        baseline: RenderModel,
    ) -> _GenerationRenderResult:
        payload = self._extract_json_object(response_text)
        reworded_payload = payload.get("reworded")
        if not isinstance(reworded_payload, list):
            change_log_payload = payload.get("change_log")
            if isinstance(change_log_payload, dict):
                reworded_payload = change_log_payload.get("reworded")

        updates = self._parse_reword_updates(reworded_payload, baseline)
        if len(updates) == 0:
            return _GenerationRenderResult(
                render_model=baseline,
                change_log=ChangeLog(added=[], removed=[], reworded=[]),
            )

        updated_model, reworded_entries = self._apply_reword_updates(baseline, updates)
        return _GenerationRenderResult(
            render_model=updated_model,
            change_log=ChangeLog(added=[], removed=[], reworded=reworded_entries),
        )

    def _parse_reword_updates(
        self,
        payload: Any,
        baseline: RenderModel,
    ) -> dict[str, tuple[str, str]]:
        baseline_text_by_id = self._bullet_text_by_id(baseline)
        if not isinstance(payload, list):
            return {}

        updates: dict[str, tuple[str, str]] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            bullet_id_raw = item.get("bullet_id", item.get("id"))
            if not isinstance(bullet_id_raw, str):
                continue
            bullet_id = bullet_id_raw.strip()
            if not bullet_id or bullet_id not in baseline_text_by_id or bullet_id in updates:
                continue

            text_raw = item.get("text", item.get("to"))
            if not isinstance(text_raw, str):
                continue
            text = " ".join(text_raw.strip().split())
            if not text:
                continue

            reason_raw = item.get("reason")
            reason = reason_raw.strip() if isinstance(reason_raw, str) else "job_alignment"
            if reason not in _ALLOWED_REWORD_REASONS:
                reason = "job_alignment"

            if text == baseline_text_by_id[bullet_id]:
                continue

            updates[bullet_id] = (text, reason)
        return updates

    def _apply_reword_updates(
        self,
        baseline: RenderModel,
        updates: dict[str, tuple[str, str]],
    ) -> tuple[RenderModel, list[RewordedEntry]]:
        changed: list[RewordedEntry] = []
        updated_sections: dict[str, list[RenderSectionEntry]] = {}
        for section_name, entries in baseline.sections.items():
            updated_entries: list[RenderSectionEntry] = []
            for entry in entries:
                updated_bullets: list[RenderBullet] = []
                for bullet in entry.bullets:
                    update = updates.get(bullet.id)
                    if update is None:
                        updated_bullets.append(bullet)
                        continue
                    to_text, reason = update
                    changed.append(
                        RewordedEntry(
                            from_text=bullet.text,
                            to_text=to_text,
                            reason=reason,
                        )
                    )
                    updated_bullets.append(RenderBullet(id=bullet.id, text=to_text))
                updated_entries.append(RenderSectionEntry(entry_id=entry.entry_id, bullets=updated_bullets))
            updated_sections[section_name] = updated_entries

        return (
            RenderModel(
                headline=baseline.headline,
                summary=baseline.summary,
                selected_experience_ids=list(baseline.selected_experience_ids),
                selected_project_ids=list(baseline.selected_project_ids),
                selected_skill_keywords=list(baseline.selected_skill_keywords),
                sections=updated_sections,
            ),
            changed,
        )

    def _extract_json_object(self, text: str) -> dict[str, Any]:
        content = text.strip()
        if content.startswith("```"):
            content = "\n".join(
                line for line in content.splitlines() if not line.strip().startswith("```")
            ).strip()
        if not content:
            raise ValueError("llm response was empty")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("llm response did not contain json object")
            parsed = json.loads(content[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("llm response json must be an object")
        return parsed

    def _bullet_text_by_id(self, render_model: RenderModel) -> dict[str, str]:
        by_id: dict[str, str] = {}
        for sections in render_model.sections.values():
            for section in sections:
                for bullet in section.bullets:
                    by_id[bullet.id] = bullet.text
        return by_id

    def _build_source_claim_index(
        self,
        render_model: RenderModel,
    ) -> dict[str, tuple[str, str, str]]:
        index: dict[str, tuple[str, str, str]] = {}
        section_source_map = (
            ("education", "education"),
            ("experience", "experience"),
            ("projects", "project"),
        )
        for section_name, source_type in section_source_map:
            for section in render_model.sections.get(section_name, []):
                for bullet in section.bullets:
                    index[bullet.id] = (source_type, section.entry_id, bullet.text)
        return index

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

    def _build_claims_map(
        self,
        render_model: RenderModel,
        *,
        source_claim_index: dict[str, tuple[str, str, str]],
    ) -> list[ClaimMapEntry]:
        claims: list[ClaimMapEntry] = []
        section_source_map = (
            ("education", "education"),
            ("experience", "experience"),
            ("projects", "project"),
        )
        for section_name, source_type in section_source_map:
            claims.extend(
                self._build_section_claims(
                    render_model=render_model,
                    section_name=section_name,
                    source_type=source_type,
                    source_claim_index=source_claim_index,
                )
            )

        return claims

    def _build_section_claims(
        self,
        *,
        render_model: RenderModel,
        section_name: str,
        source_type: str,
        source_claim_index: dict[str, tuple[str, str, str]],
    ) -> list[ClaimMapEntry]:
        claims: list[ClaimMapEntry] = []
        for section in render_model.sections.get(section_name, []):
            for bullet in section.bullets:
                source = source_claim_index.get(bullet.id)
                source_type_value = source_type if source is None else source[0]
                source_id = section.entry_id if source is None else source[1]
                evidence_text = bullet.text if source is None else source[2]
                claims.append(
                    ClaimMapEntry(
                        bullet_id=bullet.id,
                        bullet_text=bullet.text,
                        source_type=source_type_value,
                        source_id=source_id,
                        evidence_text=evidence_text,
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
