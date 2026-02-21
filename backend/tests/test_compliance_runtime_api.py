from __future__ import annotations

import json
import sqlite3
import threading
import unittest
from http.client import HTTPConnection

from app.main import create_server


class ComplianceRuntimeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/compliance-runtime-test.db"
        self.server = create_server(db_path=self.db_path, host="127.0.0.1", port=0)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _create_tmpdir(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="compliance-runtime-api-tests-")

    def _request_json(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        headers = {"Content-Type": "application/json"}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read().decode("utf-8")
        conn.close()
        return response.status, (json.loads(raw) if raw else {})

    def _capture_application(self) -> tuple[str, str]:
        status, payload = self._request_json(
            "POST",
            "/api/v1/jobs/capture",
            {
                "title": "Backend Engineer",
                "company": "Acme",
                "location": "Rochester, NY",
                "job_url": "https://www.linkedin.com/jobs/view/123",
                "description_raw": (
                    "We are hiring a Senior Backend Engineer.\n"
                    "Responsibilities: Build API services.\n"
                    "Requirements: 3+ years Python and FastAPI.\n"
                    "Preferred: AWS experience.\n"
                    "Full-time role."
                ),
                "captured_at": "2026-02-21T10:00:00Z",
            },
        )
        self.assertEqual(status, 201)
        return payload["application_id"], payload["job_posting_id"]

    def _seed_profile(self, full_name: str = "Taylor Dev") -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_profiles (
                    id, full_name, headline, summary, experiences_json, projects_json,
                    skills_json, education_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "profile-1",
                    full_name,
                    "Backend Engineer",
                    "Builds reliable APIs.",
                    json.dumps(
                        [
                            {
                                "id": "exp-1",
                                "company": "DataCo",
                                "title": "Engineer",
                                "start_date": "2021-01-01",
                                "end_date": None,
                                "bullets": [
                                    "Built Python APIs for internal analytics workloads.",
                                    "Designed SQL models for reporting.",
                                ],
                                "skills": ["Python", "SQL", "FastAPI"],
                            }
                        ]
                    ),
                    json.dumps([]),
                    json.dumps(["Python", "SQL", "FastAPI"]),
                    json.dumps([]),
                    "2026-02-21T10:00:00Z",
                ),
            )
            conn.commit()

    def test_status_patch_returns_404_for_missing_application(self) -> None:
        status, body = self._request_json(
            "PATCH",
            "/api/v1/applications/missing/status",
            {"target_status": "drafting"},
        )

        self.assertEqual(status, 404)
        self.assertIn("not found", body["detail"])

    def test_status_patch_returns_409_on_invalid_transition(self) -> None:
        application_id, _ = self._capture_application()
        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "applied"},
        )

        self.assertEqual(status, 409)
        self.assertIn("invalid transition", body["detail"])

    def test_generate_returns_422_when_profile_identity_missing(self) -> None:
        application_id, _ = self._capture_application()
        self._seed_profile(full_name="")

        status, body = self._request_json(
            "POST",
            f"/api/v1/applications/{application_id}/resume-versions/generate",
            {"template_id": "modern"},
        )

        self.assertEqual(status, 422)
        self.assertIn("blocked_reasons", body["detail"])
        self.assertIn("user profile full_name is required", body["detail"]["blocked_reasons"])

    def test_approval_gate_blocks_ready_to_apply_until_approved(self) -> None:
        application_id, _ = self._capture_application()
        self._seed_profile()

        status, _ = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "drafting"},
        )
        self.assertEqual(status, 200)

        status, generated = self._request_json(
            "POST",
            f"/api/v1/applications/{application_id}/resume-versions/generate",
            {"template_id": "modern"},
        )
        self.assertEqual(status, 201)
        resume_version_id = generated["resume_version_id"]

        status, blocked = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "ready_to_apply"},
        )
        self.assertEqual(status, 422)
        self.assertIn("approval gate failed", blocked["detail"])

        status, approved = self._request_json(
            "POST",
            f"/api/v1/resume-versions/{resume_version_id}/approve",
        )
        self.assertEqual(status, 200)
        self.assertTrue(approved["approval"]["approved"])

        status, ready = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "ready_to_apply"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(ready["application"]["status"], "ready_to_apply")

    def test_approve_returns_404_for_missing_resume_version(self) -> None:
        status, body = self._request_json(
            "POST",
            "/api/v1/resume-versions/missing-version/approve",
        )

        self.assertEqual(status, 404)
        self.assertIn("not found", body["detail"])

    def test_approve_returns_422_for_rejected_claim_version(self) -> None:
        application_id, _ = self._capture_application()

        with sqlite3.connect(self.db_path) as conn:
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
                    "ver-rejected",
                    application_id,
                    "modern",
                    f"artifacts/resumes/{application_id}/ver-rejected.pdf",
                    f"artifacts/resumes/{application_id}/ver-rejected.html",
                    json.dumps(
                        {
                            "headline": "Taylor Dev",
                            "summary": "Builds reliable APIs.",
                            "selected_experience_ids": [],
                            "selected_project_ids": [],
                            "selected_skill_keywords": [],
                            "sections": {"experience": [], "projects": []},
                        }
                    ),
                    json.dumps({"added": [], "removed": [], "reworded": []}),
                    json.dumps(
                        [
                            {
                                "bullet_id": "b-1",
                                "bullet_text": "Invented unsupported claim",
                                "source_type": "experience",
                                "source_id": "exp-1",
                                "evidence_text": "",
                                "verification_status": "rejected",
                            }
                        ]
                    ),
                    0,
                    None,
                    "2026-02-21T10:10:00Z",
                ),
            )
            conn.commit()

        status, body = self._request_json(
            "POST",
            "/api/v1/resume-versions/ver-rejected/approve",
        )
        self.assertEqual(status, 422)
        self.assertEqual(body["detail"], "unsupported claims detected")


if __name__ == "__main__":
    unittest.main()
