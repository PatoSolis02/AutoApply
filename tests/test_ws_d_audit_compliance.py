from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from autoapply.audit_compliance import (  # noqa: E402
    AuditComplianceEngine,
    ComplianceError,
    DraftBullet,
    InMemoryStore,
    ProfileItem,
    ResumeDraft,
    UserProfile,
)


class WSDComplianceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.application_id = "app-123"
        self.store = InMemoryStore()
        self.store.create_application(self.application_id, status="drafting")
        self.engine = AuditComplianceEngine(self.store)
        self.profile = UserProfile(
            full_name="Pat Doe",
            headline="Backend Engineer",
            summary="Builds reliable internal tooling",
            experiences=(
                ProfileItem(
                    id="exp-1",
                    text="Built and maintained a FastAPI backend for recruiter workflows",
                ),
            ),
            projects=(
                ProfileItem(
                    id="proj-1",
                    text="Created a resume analytics dashboard with Python and SQLite",
                ),
            ),
            skills=(ProfileItem(id="skill-python", text="Python"),),
            education=(ProfileItem(id="edu-1", text="BS Computer Science"),),
        )

    def _draft(self, bullets: tuple[DraftBullet, ...]) -> ResumeDraft:
        return ResumeDraft(
            application_id=self.application_id,
            template_id="template-basic",
            headline="Pat Doe - Backend Engineer",
            summary="Focused on correctness and maintainability",
            selected_bullets=bullets,
        )

    def test_422_when_bullet_source_is_missing(self) -> None:
        draft = self._draft(
            (
                DraftBullet(
                    bullet_id="b-1",
                    bullet_text="Built and maintained a FastAPI backend for recruiter workflows",
                    source_type="experience",
                    source_id="exp-missing",
                ),
            )
        )

        with self.assertRaises(ComplianceError) as ctx:
            self.engine.generate_resume_version(self.profile, draft)

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(self.store.resume_versions_by_application[self.application_id], [])

    def test_422_when_bullet_introduces_unsupported_claim_tokens(self) -> None:
        draft = self._draft(
            (
                DraftBullet(
                    bullet_id="b-1",
                    bullet_text="Built and maintained a FastAPI backend for blockchain trading workflows",
                    source_type="experience",
                    source_id="exp-1",
                ),
            )
        )

        with self.assertRaises(ComplianceError) as ctx:
            self.engine.generate_resume_version(self.profile, draft)

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(self.store.resume_versions_by_application[self.application_id], [])

    def test_success_persists_claims_map_change_log_and_artifact_paths(self) -> None:
        draft = self._draft(
            (
                DraftBullet(
                    bullet_id="b-1",
                    bullet_text="Built and maintained a FastAPI backend for recruiter workflows",
                    source_type="experience",
                    source_id="exp-1",
                ),
                DraftBullet(
                    bullet_id="b-2",
                    bullet_text="Created a resume analytics dashboard with Python and SQLite",
                    source_type="project",
                    source_id="proj-1",
                ),
            )
        )

        version = self.engine.generate_resume_version(self.profile, draft)
        loaded = self.store.get_resume_version(version.id)

        self.assertEqual(len(loaded.claims_map), 2)
        self.assertTrue(all(item.verification_status == "supported" for item in loaded.claims_map))
        self.assertEqual(
            loaded.change_log.added,
            (
                "Built and maintained a FastAPI backend for recruiter workflows",
                "Created a resume analytics dashboard with Python and SQLite",
            ),
        )
        self.assertEqual(loaded.change_log.removed, ())
        self.assertEqual(loaded.change_log.reworded, ())
        self.assertTrue(loaded.pdf_path.startswith(f"artifacts/resumes/{self.application_id}/"))
        self.assertTrue(loaded.pdf_path.endswith(".pdf"))
        self.assertTrue(loaded.rendered_html_path.endswith(".html"))

    def test_change_log_tracks_reworded_bullet_between_versions(self) -> None:
        v1 = self.engine.generate_resume_version(
            self.profile,
            self._draft(
                (
                    DraftBullet(
                        bullet_id="b-1",
                        bullet_text="Built and maintained a FastAPI backend for recruiter workflows",
                        source_type="experience",
                        source_id="exp-1",
                    ),
                )
            ),
        )
        self.assertEqual(v1.change_log.reworded, ())

        v2 = self.engine.generate_resume_version(
            self.profile,
            self._draft(
                (
                    DraftBullet(
                        bullet_id="b-1",
                        bullet_text="Built a FastAPI backend for recruiter workflows",
                        source_type="experience",
                        source_id="exp-1",
                        reword_reason="brevity",
                    ),
                )
            ),
        )

        self.assertEqual(len(v2.change_log.reworded), 1)
        self.assertEqual(
            v2.change_log.reworded[0].from_text,
            "Built and maintained a FastAPI backend for recruiter workflows",
        )
        self.assertEqual(v2.change_log.reworded[0].to_text, "Built a FastAPI backend for recruiter workflows")
        self.assertEqual(v2.change_log.reworded[0].reason, "brevity")

    def test_resume_version_payload_is_immutable(self) -> None:
        version = self.engine.generate_resume_version(
            self.profile,
            self._draft(
                (
                    DraftBullet(
                        bullet_id="b-1",
                        bullet_text="Built and maintained a FastAPI backend for recruiter workflows",
                        source_type="experience",
                        source_id="exp-1",
                    ),
                )
            ),
        )

        with self.assertRaises(FrozenInstanceError):
            version.template_id = "template-mutated"  # type: ignore[misc]

    def test_approval_gate_enforced_with_422_before_ready_to_apply(self) -> None:
        version = self.engine.generate_resume_version(
            self.profile,
            self._draft(
                (
                    DraftBullet(
                        bullet_id="b-1",
                        bullet_text="Built and maintained a FastAPI backend for recruiter workflows",
                        source_type="experience",
                        source_id="exp-1",
                    ),
                )
            ),
        )

        with self.assertRaises(ComplianceError) as ctx:
            self.engine.set_application_status(self.application_id, "ready_to_apply")
        self.assertEqual(ctx.exception.status_code, 422)

        before_approve = self.store.get_resume_version(version.id)
        self.engine.approve_resume_version(version.id)
        after_approve = self.store.get_resume_version(version.id)

        self.assertEqual(before_approve.claims_map, after_approve.claims_map)
        self.assertEqual(before_approve.change_log, after_approve.change_log)
        self.assertTrue(after_approve.approval.approved)

        updated = self.engine.set_application_status(self.application_id, "ready_to_apply")
        self.assertEqual(updated.status, "ready_to_apply")


if __name__ == "__main__":
    unittest.main()
