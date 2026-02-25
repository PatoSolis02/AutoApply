from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoapply.artifacts import ArtifactWriter
from autoapply.compliance import ComplianceGate
from autoapply.contracts import GenerateResumeRequest
from autoapply.llm import LlmProviderError, LlmResponse, LlmRuntime, ProviderRegistry, load_llm_config
from autoapply.repositories import InMemoryGenerateRepository
from autoapply.service import ResumeGenerationService
from autoapply.tailoring import TailoringEngine
from tests.fixtures import sample_application, sample_job_posting, sample_user_profile


def _runtime_with_llm_response(response_text: str) -> LlmRuntime:
    class _Client:
        provider = "openai"

        def complete(self, request):
            return LlmResponse(
                text=response_text,
                provider="openai",
                model=request.model,
                prompt_version=request.prompt.version,
            )

    registry = ProviderRegistry()
    registry.register("openai", lambda _config: _Client())
    return LlmRuntime(
        load_llm_config(
            {
                "AUTOAPPLY_LLM_ENABLED": "true",
                "AUTOAPPLY_LLM_PROVIDER": "openai",
                "AUTOAPPLY_OPENAI_API_KEY": "secret",
            }
        ),
        provider_registry=registry,
    )


def _runtime_with_provider_error() -> LlmRuntime:
    class _Client:
        provider = "openai"

        def complete(self, request):
            raise LlmProviderError("provider unavailable")

    registry = ProviderRegistry()
    registry.register("openai", lambda _config: _Client())
    return LlmRuntime(
        load_llm_config(
            {
                "AUTOAPPLY_LLM_ENABLED": "true",
                "AUTOAPPLY_LLM_PROVIDER": "openai",
                "AUTOAPPLY_OPENAI_API_KEY": "secret",
            }
        ),
        provider_registry=registry,
    )


class GenerationPipelineTests(unittest.TestCase):
    def test_artifacts_written_to_contract_paths_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            writer = ArtifactWriter(workspace_root=root)
            engine = TailoringEngine()
            profile = sample_user_profile()
            job_posting = sample_job_posting()
            model = engine.build_render_model(profile, job_posting)

            html_rel, pdf_rel = writer.write_resume_artifacts(
                application_id="app-1",
                resume_version_id="ver-1",
                render_model=model,
            )
            html_abs = root / html_rel
            pdf_abs = root / pdf_rel

            self.assertEqual(html_rel, "artifacts/resumes/app-1/ver-1.html")
            self.assertEqual(pdf_rel, "artifacts/resumes/app-1/ver-1.pdf")
            self.assertTrue(html_abs.exists())
            self.assertTrue(pdf_abs.exists())
            first_pdf = pdf_abs.read_bytes()

            writer.write_resume_artifacts(
                application_id="app-1",
                resume_version_id="ver-1",
                render_model=model,
            )
            second_pdf = pdf_abs.read_bytes()
            self.assertEqual(first_pdf, second_pdf)
            self.assertTrue(second_pdf.startswith(b"%PDF-1.4"))

    def test_generation_blocks_with_422_when_profile_identity_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = sample_user_profile()
            bad_profile = profile.__class__(
                id=profile.id,
                full_name="",
                headline=profile.headline,
                summary=profile.summary,
                experiences=profile.experiences,
                projects=profile.projects,
                skills=profile.skills,
                education=profile.education,
                updated_at=profile.updated_at,
            )
            app = sample_application()
            repo = InMemoryGenerateRepository(
                applications={app.id: app},
                job_postings_by_app_id={app.id: sample_job_posting(app.id)},
                user_profile=bad_profile,
            )
            service = ResumeGenerationService(
                repository=repo,
                tailoring_engine=TailoringEngine(),
                artifact_writer=ArtifactWriter(Path(tmpdir)),
                compliance_gate=ComplianceGate(),
            )

            outcome = service.generate_resume_version(app.id, GenerateResumeRequest(template_id="modern"))
            self.assertEqual(outcome.status_code, 422)
            self.assertEqual(outcome.result.resume_version_id, "")
            self.assertIn("user profile full_name is required", outcome.result.blocked_reasons)
            self.assertEqual(repo.get_resume_versions_for_application(app.id), [])


class GenerationServiceSuccessTests(unittest.TestCase):
    def test_generation_persists_unapproved_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = sample_application()
            repo = InMemoryGenerateRepository(
                applications={app.id: app},
                job_postings_by_app_id={app.id: sample_job_posting(app.id)},
                user_profile=sample_user_profile(),
            )
            service = ResumeGenerationService(
                repository=repo,
                tailoring_engine=TailoringEngine(),
                artifact_writer=ArtifactWriter(Path(tmpdir)),
                compliance_gate=ComplianceGate(),
            )

            outcome = service.generate_resume_version(app.id, GenerateResumeRequest(template_id="modern"))
            self.assertEqual(outcome.status_code, 201)
            self.assertEqual(outcome.result.blocked_reasons, [])

            stored = repo.get_resume_versions_for_application(app.id)
            self.assertEqual(len(stored), 1)
            version = stored[0]
            self.assertFalse(version.approval.approved)
            self.assertIsNone(version.approval.approved_at)
            self.assertTrue(version.pdf_path.endswith(f"{version.id}.pdf"))
            self.assertTrue(version.rendered_html_path.endswith(f"{version.id}.html"))
            self.assertTrue(version.claims_map)


class GenerationLlmContractTests(unittest.TestCase):
    def test_llm_success_rewords_bullets_and_preserves_claim_evidence_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = sample_user_profile()
            app = sample_application()
            posting = sample_job_posting(app.id)
            baseline_model = TailoringEngine().build_render_model(profile, posting)
            source_bullet = baseline_model.sections["experience"][0].bullets[0]
            rewritten_text = "Built Python API services for analytics with clear observability coverage."

            llm_payload = json.dumps(
                {
                    "reworded": [
                        {
                            "bullet_id": source_bullet.id,
                            "text": rewritten_text,
                            "reason": "job_alignment",
                        }
                    ]
                }
            )
            repo = InMemoryGenerateRepository(
                applications={app.id: app},
                job_postings_by_app_id={app.id: posting},
                user_profile=profile,
            )
            service = ResumeGenerationService(
                repository=repo,
                tailoring_engine=TailoringEngine(),
                artifact_writer=ArtifactWriter(Path(tmpdir)),
                compliance_gate=ComplianceGate(),
                llm_runtime=_runtime_with_llm_response(llm_payload),
            )

            outcome = service.generate_resume_version(app.id, GenerateResumeRequest(template_id="modern"))
            self.assertEqual(outcome.status_code, 201)

            version = repo.get_resume_versions_for_application(app.id)[0]
            self.assertEqual(len(version.change_log.reworded), 1)
            self.assertEqual(version.change_log.reworded[0].from_text, source_bullet.text)
            self.assertEqual(version.change_log.reworded[0].to_text, rewritten_text)
            self.assertEqual(version.change_log.reworded[0].reason, "job_alignment")

            matching_claim = next(
                claim for claim in version.claims_map if claim.bullet_id == source_bullet.id
            )
            self.assertEqual(matching_claim.bullet_text, rewritten_text)
            self.assertEqual(matching_claim.evidence_text, source_bullet.text)
            self.assertEqual(matching_claim.source_id, "exp-1")
            self.assertEqual(matching_claim.verification_status, "supported")
            self.assertFalse(version.approval.approved)

    def test_llm_provider_failure_falls_back_to_deterministic_generation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = sample_user_profile()
            app = sample_application()
            posting = sample_job_posting(app.id)
            deterministic_model = TailoringEngine().build_render_model(profile, posting)
            repo = InMemoryGenerateRepository(
                applications={app.id: app},
                job_postings_by_app_id={app.id: posting},
                user_profile=profile,
            )
            service = ResumeGenerationService(
                repository=repo,
                tailoring_engine=TailoringEngine(),
                artifact_writer=ArtifactWriter(Path(tmpdir)),
                compliance_gate=ComplianceGate(),
                llm_runtime=_runtime_with_provider_error(),
            )

            outcome = service.generate_resume_version(app.id, GenerateResumeRequest(template_id="modern"))
            self.assertEqual(outcome.status_code, 201)

            version = repo.get_resume_versions_for_application(app.id)[0]
            self.assertEqual(version.render_model_json, deterministic_model)
            self.assertEqual(version.change_log.reworded, [])
            self.assertTrue(version.claims_map)


if __name__ == "__main__":
    unittest.main()
