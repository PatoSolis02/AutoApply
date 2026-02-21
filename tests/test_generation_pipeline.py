from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoapply.artifacts import ArtifactWriter
from autoapply.compliance import ComplianceGate
from autoapply.contracts import GenerateResumeRequest
from autoapply.repositories import InMemoryGenerateRepository
from autoapply.service import ResumeGenerationService
from autoapply.tailoring import TailoringEngine
from tests.fixtures import sample_application, sample_job_posting, sample_user_profile


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


if __name__ == "__main__":
    unittest.main()

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
